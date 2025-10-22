"""
services/stt_service.py
-----------------------
Speech-to-Text service for Persian audio transcription using OpenAI Whisper
"""

import os
import asyncio
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
import hashlib

from services.base_service import BaseService
from services.cache_service import get_cache_service, CacheService
from config.settings import STTSettings, FeatureFlags, get_stt_available
from utils.exceptions import ServiceError

class STTService(BaseService):
    """Persian Speech-to-Text service using OpenAI Whisper"""
    
    def __init__(self, repositories=None):
        super().__init__(repositories)
        self.model = None
        self.model_loaded = False
        self.available = get_stt_available()
        self.cache_service = get_cache_service()
        
        # Ensure audio directory exists
        STTSettings.ensure_directories()
    
    async def initialize(self) -> bool:
        """
        Initialize Whisper model from HuggingFace (matching sentiment pattern)
        
        Returns:
            True if initialization successful, False otherwise
        """
        if not self.available:
            self.logger.warning("STT not available - whisper not installed")
            return False
        
        if self.model_loaded:
            return True
        
        try:
            self.logger.info(f"Loading Whisper model: {STTSettings.MODEL_NAME}")
            
            from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline
            import torch
            
            # Prepare authentication token if available
            use_auth_token = STTSettings.HF_TOKEN if STTSettings.HF_TOKEN else None
            
            # Determine device
            device = "cuda:0" if STTSettings.USE_GPU and torch.cuda.is_available() else "cpu"
            torch_dtype = torch.float16 if device != "cpu" else torch.float32
            
            self.logger.info(f"Using device: {device}")
            self.logger.info(f"Cache directory: {STTSettings.CACHE_DIR}")
            
            # Load model - will download if not in cache
            self.logger.info("Loading model (downloading if needed, this may take a while)...")
            model = AutoModelForSpeechSeq2Seq.from_pretrained(
                STTSettings.MODEL_NAME,
                torch_dtype=torch_dtype,
                low_cpu_mem_usage=True,
                use_safetensors=True,
                cache_dir=str(STTSettings.CACHE_DIR),
                token=use_auth_token  # Use HF token if available
            )
            model.to(device)
            
            # Load processor
            self.logger.info("Loading processor...")
            processor = AutoProcessor.from_pretrained(
                STTSettings.MODEL_NAME,
                cache_dir=str(STTSettings.CACHE_DIR),
                token=use_auth_token
            )
            
            # Create pipeline
            self.logger.info("Creating pipeline...")
            self.pipeline = pipeline(
                "automatic-speech-recognition",
                model=model,
                tokenizer=processor.tokenizer,
                feature_extractor=processor.feature_extractor,
                max_new_tokens=128,
                chunk_length_s=STTSettings.CHUNK_LENGTH_S,
                batch_size=STTSettings.BATCH_SIZE,
                return_timestamps=STTSettings.RETURN_TIMESTAMPS,
                torch_dtype=torch_dtype,
                device=device,
            )
            
            self.model = model
            self.processor = processor
            self.model_loaded = True
            
            # Count parameters
            param_count = sum(p.numel() for p in model.parameters())
            
            self.logger.info(f"✅ Whisper model loaded successfully!")
            self.logger.info(f"   Model: {STTSettings.MODEL_NAME}")
            self.logger.info(f"   Device: {device}")
            self.logger.info(f"   Parameters: {param_count:,}")
            self.logger.info(f"   Cache: {STTSettings.CACHE_DIR}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to load Whisper model: {e}")
            import traceback
            traceback.print_exc()
            raise ServiceError(f"STT model initialization failed: {e}")
    
    def _get_audio_hash(self, audio_path: Union[str, Path]) -> str:
        """Generate hash for audio file for caching"""
        audio_path = Path(audio_path)
        
        # Use file path + modification time for hash
        hash_string = f"{audio_path.name}_{audio_path.stat().st_mtime}"
        return hashlib.md5(hash_string.encode()).hexdigest()
    
    async def transcribe_audio(
        self,
        audio_path: Union[str, Path],
        language: Optional[str] = None,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Transcribe Persian audio to text
        
        Args:
            audio_path: Path to audio file
            language: Language code (default: 'fa' for Persian)
            use_cache: Whether to use cached transcriptions
            
        Returns:
            Dictionary containing transcription and metadata
        """
        if not self.model_loaded:
            await self.initialize()
        
        audio_path = Path(audio_path)
        language = language or STTSettings.LANGUAGE
        
        # Check file exists
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        
        # Check cache first
        if use_cache and STTSettings.CACHE_TRANSCRIPTIONS:
            audio_hash = self._get_audio_hash(audio_path)
            cache_key = f"stt:transcription:{audio_hash}"
            
            cached_result = self.cache_service.get(cache_key)
            if cached_result:
                self.logger.info(f"Retrieved transcription from cache: {audio_path.name}")
                return cached_result
        
        try:
            self.logger.info(f"Transcribing audio: {audio_path.name}")
            
            # Transcribe using Whisper
            result = self.pipeline(
            str(audio_path),
            batch_size=STTSettings.BATCH_SIZE,
            generate_kwargs={
                "language": language or STTSettings.LANGUAGE,
                "task": STTSettings.TASK,
                "num_beams": STTSettings.BEAM_SIZE,
                "temperature": STTSettings.TEMPERATURE,
            }
        )
            
            # Prepare result
            transcription_result = {
                'transcription': result['text'].strip(),
                'segments': result.get('segments', []),
                'language': result.get('language', language),
                'audio_file': audio_path.name,
                'model': f"whisper-{STTSettings.MODEL_SIZE}",
                'duration_seconds': sum(seg['end'] - seg['start'] for seg in result.get('segments', [])),
                'transcribed_at': datetime.now().isoformat()
            }
            
            # Cache result
            if use_cache and STTSettings.CACHE_TRANSCRIPTIONS:
                self.cache_service.set(
                    cache_key,
                    transcription_result,
                    ttl=STTSettings.CACHE_TTL_SECONDS
                )
            
            self.logger.info(f"Transcription complete: {len(transcription_result['transcription'])} characters")
            return transcription_result
            
        except Exception as e:
            self.logger.error(f"Transcription failed: {e}")
            raise ServiceError(f"Transcription failed: {e}")
    
    async def transcribe_batch(
        self,
        audio_paths: List[Union[str, Path]],
        language: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Transcribe multiple audio files
        
        Args:
            audio_paths: List of audio file paths
            language: Language code
            
        Returns:
            List of transcription results
        """
        results = []
        
        for audio_path in audio_paths:
            try:
                result = await self.transcribe_audio(audio_path, language)
                results.append(result)
            except Exception as e:
                self.logger.error(f"Failed to transcribe {audio_path}: {e}")
                results.append({
                    'audio_file': Path(audio_path).name,
                    'error': str(e),
                    'transcription': None
                })
        
        return results
    
    def get_supported_formats(self) -> List[str]:
        """Get list of supported audio formats"""
        return STTSettings.SUPPORTED_FORMATS
    
    def validate_audio_file(self, audio_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Validate audio file
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Validation result with status and details
        """
        audio_path = Path(audio_path)
        
        result = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'details': {}
        }
        
        # Check file exists
        if not audio_path.exists():
            result['valid'] = False
            result['errors'].append(f"File not found: {audio_path}")
            return result
        
        # Check file extension
        if audio_path.suffix.lower() not in STTSettings.SUPPORTED_FORMATS:
            result['valid'] = False
            result['errors'].append(
                f"Unsupported format: {audio_path.suffix}. "
                f"Supported: {', '.join(STTSettings.SUPPORTED_FORMATS)}"
            )
        
        # Check file size
        file_size_mb = audio_path.stat().st_size / (1024 * 1024)
        result['details']['size_mb'] = round(file_size_mb, 2)
        
        if file_size_mb > STTSettings.MAX_AUDIO_SIZE_MB:
            result['valid'] = False
            result['errors'].append(
                f"File too large: {file_size_mb:.2f}MB "
                f"(max: {STTSettings.MAX_AUDIO_SIZE_MB}MB)"
            )
        elif file_size_mb > STTSettings.MAX_AUDIO_SIZE_MB * 0.8:
            result['warnings'].append(
                f"File size close to limit: {file_size_mb:.2f}MB"
            )
        
        return result
    
    async def cleanup(self):
        """Cleanup resources"""
        self.logger.info("Cleaning up STT service resources")
        
        if self.model is not None:
            del self.model
            self.model = None
        
        self.model_loaded = False
        
        # Clear GPU cache if using CUDA
        try:
            import torch
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except:
            pass


# Singleton instance
_stt_service_instance: Optional[STTService] = None

def get_stt_service(repositories=None) -> STTService:
    """Get or create STT service singleton instance"""
    global _stt_service_instance
    
    if _stt_service_instance is None:
        _stt_service_instance = STTService(repositories)
    
    return _stt_service_instance