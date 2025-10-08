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
        Initialize Whisper model
        
        Returns:
            True if initialization successful, False otherwise
        """
        if not self.available:
            self.logger.warning("STT not available - whisper not installed")
            return False
        
        if self.model_loaded:
            return True
        
        try:
            self.logger.info(f"Loading Whisper model: {STTSettings.MODEL_SIZE}")
            
            import whisper
            import torch
            "vhdm/whisper-large-fa-v1"
            # Load model
            device = "cuda" if STTSettings.USE_GPU and torch.cuda.is_available() else "cpu"
            self.model = whisper.load_model(
                STTSettings.MODEL_SIZE,
                device=device
            )
            
            self.model_loaded = True
            self.logger.info(f"Whisper model loaded successfully on {device}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to load Whisper model: {e}")
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
            result = self.model.transcribe(
                str(audio_path),
                language=language,
                task=STTSettings.TASK,
                beam_size=STTSettings.BEAM_SIZE,
                best_of=STTSettings.BEST_OF,
                temperature=STTSettings.TEMPERATURE,
                fp16=STTSettings.FP16 if STTSettings.USE_GPU else False
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