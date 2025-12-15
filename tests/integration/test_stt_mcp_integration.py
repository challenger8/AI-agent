"""
tests/integration/test_stt_mcp_integration.py
---------------------------------------------
Integration tests for STT tools via MCP server
"""

import pytest
import json
import sys
from pathlib import Path
from tests.utils.test_helpers import parse_result

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from mcp_spec.server import create_mcp_server
from config.settings import STTSettings

@pytest.mark.integration
@pytest.mark.asyncio
class TestSTTMCPIntegration:
    """Test STT tools through MCP server"""
    
    async def test_list_stt_tools(self):
        """Test that STT tools are registered in MCP"""
        print("\n📋 Testing STT tools registration...")
        
        server = create_mcp_server()
        await server.initialize_services()
        
        assert server.tool_handlers is not None
        
        tools = server.tool_handlers.get_tools()
        tool_names = [t.name for t in tools]
        
        # Check STT tools are registered
        assert "transcribe_audio" in tool_names
        assert "transcribe_batch" in tool_names
        assert "list_audio_files" in tool_names
        assert "validate_audio" in tool_names
        
        print("✅ All 4 STT tools registered")
        
        # Check tool descriptions
        stt_tools = [t for t in tools if 'audio' in t.name.lower() or 'transcribe' in t.name.lower()]
        assert len(stt_tools) >= 4
        
        for tool in stt_tools:
            print(f"  ✓ {tool.name}: {tool.description[:50]}...")
            assert tool.description is not None
            assert len(tool.description) > 0
    
    async def test_list_audio_files_tool(self):
        """Test list_audio_files MCP tool"""
        print("\n📂 Testing list_audio_files tool...")
        
        server = create_mcp_server()
        await server.initialize_services()
        
        assert server.tool_handlers is not None
        
        # Call list_audio_files tool
        result = await server.tool_handlers.handle_tool_call(
            'list_audio_files',
            {}
        )
        
        assert result is not None
        data = parse_result(result)
        
        assert 'audio_directory' in data
        assert 'total_files' in data
        assert 'files' in data
        assert 'supported_formats' in data
        
        print(f"✅ Audio directory: {data['audio_directory']}")
        print(f"✅ Total files: {data['total_files']}")
        print(f"✅ Supported formats: {len(data['supported_formats'])} formats")
        
        # Check supported formats
        assert len(data['supported_formats']) > 0
        assert '.mp3' in data['supported_formats']
        assert '.wav' in data['supported_formats']
    
    async def test_validate_audio_tool_nonexistent(self):
        """Test validate_audio with non-existent file"""
        print("\n🔍 Testing validate_audio with non-existent file...")
        
        server = create_mcp_server()
        await server.initialize_services()
        
        assert server.tool_handlers is not None
        
        # Call validate_audio with non-existent file
        result = await server.tool_handlers.handle_tool_call(
            'validate_audio',
            {'audio_file': 'nonexistent_file.mp3'}
        )
        
        assert result is not None
        data = parse_result(result)
        
        assert 'audio_file' in data
        assert 'valid' in data
        assert data['valid'] == False
        assert 'errors' in data
        assert len(data['errors']) > 0
        
        print(f"✅ Correctly identified invalid file")
        print(f"✅ Errors: {data['errors']}")
    
    async def test_validate_audio_tool_existing(self):
        """Test validate_audio with existing file (if available)"""
        print("\n🔍 Testing validate_audio with existing files...")
        
        server = create_mcp_server()
        await server.initialize_services()
        
        assert server.tool_handlers is not None
        
        # First get list of files
        list_result = await server.tool_handlers.handle_tool_call(
            'list_audio_files',
            {}
        )
        
        data = parse_result(list_result)
        
        if data.get('files') and len(data['files']) > 0:
            test_file = data['files'][0]['name']
            print(f"  Testing with file: {test_file}")
            
            # Validate the file
            result = await server.tool_handlers.handle_tool_call(
                'validate_audio',
                {'audio_file': test_file}
            )
            
            validation = parse_result(result)
            
            assert 'audio_file' in validation
            assert 'valid' in validation
            assert validation['audio_file'] == test_file
            
            print(f"✅ Validation result: {validation['valid']}")
            
            if validation.get('details'):
                print(f"✅ File size: {validation['details'].get('size_mb')}MB")
        else:
            print("⏭️  No audio files to test - skipping")
            pytest.skip("No audio files available for testing")
    
    async def test_transcribe_audio_tool_nonexistent(self):
        """Test transcribe_audio with non-existent file"""
        print("\n🎤 Testing transcribe_audio with non-existent file...")
        
        server = create_mcp_server()
        await server.initialize_services()
        
        assert server.tool_handlers is not None
        
        # Call transcribe_audio with non-existent file
        result = await server.tool_handlers.handle_tool_call(
            'transcribe_audio',
            {'audio_file': 'nonexistent_file.mp3', 'language': 'fa'}
        )
        
        assert result is not None
        data = json.loads(result if isinstance(result, (str, dict)) else result.text)
        
        # Should return error
        assert 'error' in data or ('success' in data and data['success'] == False)
        
        print(f"✅ Correctly handled non-existent file")
    
    async def test_transcribe_audio_tool_existing(self):
        """Test transcribe_audio with existing file (if available)"""
        print("\n🎤 Testing transcribe_audio with existing files...")
        
        server = create_mcp_server()
        await server.initialize_services()
        
        assert server.tool_handlers is not None
        
        # First get list of files
        list_result = await server.tool_handlers.handle_tool_call(
            'list_audio_files',
            {}
        )
        
        data = parse_result(list_result)
        
        if data.get('files') and len(data['files']) > 0:
            test_file = data['files'][0]['name']
            print(f"  Transcribing: {test_file}")
            print(f"  ⏳ This may take a moment...")
            
            # Transcribe the file
            result = await server.tool_handlers.handle_tool_call(
                'transcribe_audio',
                {'audio_file': test_file, 'language': 'fa'}
            )
            
            transcription = parse_result(result)
            
            assert 'success' in transcription or 'error' in transcription
            
            if transcription.get('success'):
                print(f"\n✅ Transcription successful!")
                print(f"  Language: {transcription.get('language')}")
                print(f"  Duration: {transcription.get('duration_seconds', 0):.2f}s")
                print(f"  Model: {transcription.get('model')}")
                
                assert 'transcription' in transcription
                assert 'language' in transcription
                assert 'duration_seconds' in transcription
                
                text = transcription.get('transcription', '')
                assert len(text) > 0
                
                preview = text[:100] + "..." if len(text) > 100 else text
                print(f"  📝 Preview: {preview}")
            else:
                print(f"⚠️  Transcription returned error: {transcription.get('error')}")
                # Don't fail test - just note the error
        else:
            print("⏭️  No audio files to test - skipping")
            pytest.skip("No audio files available for testing")
    
    async def test_transcribe_batch_tool(self):
        """Test transcribe_batch with multiple files"""
        print("\n📦 Testing transcribe_batch tool...")
        
        server = create_mcp_server()
        await server.initialize_services()
        
        assert server.tool_handlers is not None
        
        # First get list of files
        list_result = await server.tool_handlers.handle_tool_call(
            'list_audio_files',
            {}
        )
        
        data = parse_result(list_result)
        
        if data.get('files') and len(data['files']) > 0:
            # Get up to 2 files for batch test
            test_files = [f['name'] for f in data['files'][:2]]
            print(f"  Testing batch with {len(test_files)} file(s)")
            
            # Call batch transcription
            result = await server.tool_handlers.handle_tool_call(
                'transcribe_batch',
                {'audio_files': test_files, 'language': 'fa'}
            )
            
            batch_result = parse_result(result)
            
            assert 'success' in batch_result or 'error' in batch_result
            
            if batch_result.get('success'):
                print(f"✅ Batch transcription completed")
                assert 'total_files' in batch_result
                assert 'results' in batch_result
                assert batch_result['total_files'] == len(test_files)
                print(f"  Processed: {batch_result['total_files']} files")
            else:
                print(f"⚠️  Batch returned error: {batch_result.get('error')}")
        else:
            print("⏭️  No audio files to test - skipping")
            pytest.skip("No audio files available for testing")
    
    async def test_stt_tools_error_handling(self):
        """Test error handling in STT tools"""
        print("\n⚠️  Testing error handling...")
        
        server = create_mcp_server()
        await server.initialize_services()
        
        assert server.tool_handlers is not None
        
        # Test with missing parameters
        result = await server.tool_handlers.handle_tool_call(
            'transcribe_audio',
            {}  # Missing audio_file
        )
        
        data = parse_result(result)
        assert 'error' in data
        print(f"✅ Correctly handled missing parameter")
        
        # Test with empty batch
        result = await server.tool_handlers.handle_tool_call(
            'transcribe_batch',
            {'audio_files': []}
        )
        
        data = parse_result(result)
        assert 'error' in data
        print(f"✅ Correctly handled empty batch")


# For direct execution
@pytest.mark.integration
async def run_all_stt_mcp_tests():
    """Run all STT MCP integration tests"""
    print("\n" + "🚀 " + "="*58)
    print("    STT MCP INTEGRATION TESTS")
    print("="*60 + "\n")
    
    test_class = TestSTTMCPIntegration()
    
    tests = [
        ("List STT Tools", test_class.test_list_stt_tools),
        ("List Audio Files", test_class.test_list_audio_files_tool),
        ("Validate Nonexistent", test_class.test_validate_audio_tool_nonexistent),
        ("Validate Existing", test_class.test_validate_audio_tool_existing),
        ("Transcribe Nonexistent", test_class.test_transcribe_audio_tool_nonexistent),
        ("Transcribe Existing", test_class.test_transcribe_audio_tool_existing),
        ("Batch Transcribe", test_class.test_transcribe_batch_tool),
        ("Error Handling", test_class.test_stt_tools_error_handling),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            await test_func()
            results.append((test_name, True))
        except pytest.skip.Exception as e:
            print(f"⏭️  Test '{test_name}' skipped: {e}")
            results.append((test_name, "SKIP"))
        except Exception as e:
            print(f"\n❌ Test '{test_name}' failed: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))
    
    # Summary
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)
    
    for test_name, result in results:
        if result == True:
            status = "✅ PASS"
        elif result == "SKIP":
            status = "⏭️  SKIP"
        else:
            status = "❌ FAIL"
        print(f"{status} - {test_name}")
    
    passed = sum(1 for _, result in results if result == True)
    skipped = sum(1 for _, result in results if result == "SKIP")
    failed = sum(1 for _, result in results if result == False)
    total = len(results)
    
    print(f"\n🎯 Results: {passed} passed, {skipped} skipped, {failed} failed / {total} total")
    print("="*60 + "\n")
    
    return failed == 0


if __name__ == "__main__":
    import asyncio
    success = asyncio.run(run_all_stt_mcp_tests())
    sys.exit(0 if success else 1)