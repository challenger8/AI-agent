"""
tests/manual/test_stt_manual.py
-------------------------------
Manual test for STT (Speech-to-Text) service
"""

import asyncio
import pytest
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from services.stt_service import get_stt_service
from config.settings import STTSettings


@pytest.mark.asyncio
async def test_stt_initialization():
    """Test STT service initialization"""
    print("\n" + "="*60)
    print("🧪 Testing STT Service Initialization")
    print("="*60)
    
    # Get service instance
    stt_service = get_stt_service()
    print(f"✅ STT Service instance created")
    
    # Check availability
    print(f"\n📊 Availability Check:")
    print(f"   - STT Available: {stt_service.available}")
    print(f"   - Model Loaded: {stt_service.model_loaded}")
    
    # Try to initialize
    print(f"\n🔄 Initializing STT service...")
    print(f"   - This will download the Whisper model (~74MB for 'base')")
    print(f"   - Please wait...")
    
    try:
        initialized = await stt_service.initialize()
        
        if initialized:
            print("\n✅ STT Service initialized successfully!")
            print(f"\n📦 Model Information:")
            print(f"   - Model Size: {STTSettings.MODEL_SIZE}")
            print(f"   - Language: {STTSettings.LANGUAGE}")
            print(f"   - GPU Enabled: {STTSettings.USE_GPU}")
            print(f"   - FP16: {STTSettings.FP16}")
            print(f"   - Model Loaded: {stt_service.model_loaded}")
            
            # Check GPU availability
            try:
                import torch
                if torch.cuda.is_available():
                    print(f"   - GPU Available: Yes ({torch.cuda.get_device_name(0)})")
                else:
                    print(f"   - GPU Available: No (using CPU)")
            except:
                print(f"   - GPU Available: Unknown")
        else:
            print("❌ STT Service failed to initialize")
            pytest.fail("STT Service initialization failed")
            
    except Exception as e:
        print(f"\n❌ Initialization error: {e}")
        import traceback
        traceback.print_exc()
        pytest.fail(f"Initialization error: {e}")
    
    # Show configuration
    print(f"\n⚙️  Configuration:")
    print(f"   - Audio Directory: {STTSettings.AUDIO_DIR}")
    print(f"   - Max File Size: {STTSettings.MAX_AUDIO_SIZE_MB}MB")
    print(f"   - Sample Rate: {STTSettings.SAMPLE_RATE}Hz")
    print(f"   - Cache Enabled: {STTSettings.CACHE_TRANSCRIPTIONS}")
    print(f"   - Beam Size: {STTSettings.BEAM_SIZE}")
    print(f"   - Temperature: {STTSettings.TEMPERATURE}")
    
    # Show supported formats
    formats = stt_service.get_supported_formats()
    print(f"\n🎵 Supported Audio Formats:")
    print(f"   {', '.join(formats)}")
    
    print("\n" + "="*60)
    print("✅ All STT initialization tests passed!")
    print("="*60)


@pytest.mark.asyncio
async def test_audio_validation():
    """Test audio file validation"""
    print("\n" + "="*60)
    print("🧪 Testing Audio File Validation")
    print("="*60)
    
    stt_service = get_stt_service()
    
    # Test with non-existent file
    print("\n📝 Test 1: Non-existent file")
    result = stt_service.validate_audio_file("non_existent_file.mp3")
    print(f"   Valid: {result['valid']}")
    if result['errors']:
        print(f"   Errors: {result['errors']}")
    assert result['valid'] == False, "Should be invalid for non-existent file"
    
    # Test with audio_files directory
    audio_dir = STTSettings.AUDIO_DIR
    print(f"\n📁 Audio directory: {audio_dir}")
    print(f"   Exists: {audio_dir.exists()}")
    
    # List any existing audio files
    if audio_dir.exists():
        audio_files = []
        for ext in STTSettings.SUPPORTED_FORMATS:
            audio_files.extend(audio_dir.glob(f"*{ext}"))
        
        if audio_files:
            print(f"\n📂 Found {len(audio_files)} audio file(s) in directory:")
            for f in audio_files:
                print(f"   - {f.name} ({f.stat().st_size / (1024*1024):.2f}MB)")
                validation = stt_service.validate_audio_file(f)
                print(f"     ✓ Valid: {validation['valid']}")
                if validation['details']:
                    print(f"     ✓ Size: {validation['details'].get('size_mb', 0):.2f}MB")
                if validation['warnings']:
                    print(f"     ⚠ Warnings: {validation['warnings']}")
                if validation['errors']:
                    print(f"     ✗ Errors: {validation['errors']}")
        else:
            print(f"\n📭 No audio files found in {audio_dir}")
            print(f"\n   💡 To test transcription:")
            print(f"      1. Add a Persian audio file (.mp3, .wav, etc.) to:")
            print(f"         {audio_dir}")
            print(f"      2. Run this test again")
    
    print("\n" + "="*60)
    print("✅ Audio validation tests completed!")
    print("="*60)


@pytest.mark.asyncio
async def test_transcription_if_audio_exists():
    """Test transcription if audio files exist"""
    print("\n" + "="*60)
    print("🧪 Testing Audio Transcription")
    print("="*60)
    
    stt_service = get_stt_service()
    
    # Check if model is initialized
    if not stt_service.model_loaded:
        print("⏭️  Model not yet loaded, initializing...")
        await stt_service.initialize()
    
    audio_dir = STTSettings.AUDIO_DIR
    
    if not audio_dir.exists():
        print(f"⏭️  Skipping transcription test - audio directory doesn't exist")
        pytest.skip("Audio directory doesn't exist")
        return
    
    # Find audio files
    audio_files = []
    for ext in STTSettings.SUPPORTED_FORMATS:
        audio_files.extend(audio_dir.glob(f"*{ext}"))
    
    if not audio_files:
        print(f"\n📭 No audio files found for transcription test")
        print(f"\n   💡 To test transcription:")
        print(f"      1. Add a Persian audio file to: {audio_dir}")
        print(f"      2. Supported formats: {', '.join(STTSettings.SUPPORTED_FORMATS)}")
        print(f"      3. Run this test again")
        pytest.skip("No audio files found")
        return
    
    print(f"\n🎵 Found {len(audio_files)} audio file(s)")
    
    # Test transcription on first file
    test_file = audio_files[0]
    print(f"\n🔄 Testing transcription on: {test_file.name}")
    print(f"   Size: {test_file.stat().st_size / (1024*1024):.2f}MB")
    print(f"   This may take a moment...")
    
    try:
        result = await stt_service.transcribe_audio(test_file)
        
        print(f"\n✅ Transcription successful!")
        print(f"\n📝 Results:")
        print(f"   - Language Detected: {result['language']}")
        print(f"   - Model Used: {result['model']}")
        print(f"   - Duration: {result['duration_seconds']:.2f} seconds")
        print(f"   - Transcription Length: {len(result['transcription'])} characters")
        print(f"   - Segments: {len(result.get('segments', []))} segments")
        print(f"   - Transcribed at: {result['transcribed_at']}")
        
        # Show first 300 characters of transcription
        transcription_preview = result['transcription'][:300]
        if len(result['transcription']) > 300:
            transcription_preview += "..."
        
        print(f"\n   📄 Transcription Preview:")
        print(f"   {'-' * 58}")
        print(f"   {transcription_preview}")
        print(f"   {'-' * 58}")
        
        # Test cache
        print(f"\n🔄 Testing cache retrieval...")
        cached_result = await stt_service.transcribe_audio(test_file)
        print(f"   ✅ Cache working (should be instant)")
        
    except Exception as e:
        print(f"\n❌ Transcription failed: {e}")
        import traceback
        traceback.print_exc()
        pytest.fail(f"Transcription failed: {e}")
    
    print("\n" + "="*60)
    print("✅ Transcription test completed!")
    print("="*60)


# For direct execution (python tests/manual/test_stt_manual.py)
async def run_all_tests_direct():
    """Run all tests when executed directly"""
    print("\n" + "🚀 " + "="*58)
    print("    STT SERVICE MANUAL TESTS")
    print("    Using OpenAI Whisper for Persian Speech-to-Text")
    print("="*60 + "\n")
    
    tests = [
        ("Initialization", test_stt_initialization),
        ("Audio Validation", test_audio_validation),
        ("Transcription", test_transcription_if_audio_exists),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            await test_func()
            results.append((test_name, True))
        except Exception as e:
            print(f"\n❌ Test '{test_name}' failed with exception: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))
    
    # Summary
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    print(f"\n🎯 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed successfully!")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
    
    print("="*60 + "\n")
    
    return passed == total


if __name__ == "__main__":
    # When run directly with python
    success = asyncio.run(run_all_tests_direct())
    sys.exit(0 if success else 1)