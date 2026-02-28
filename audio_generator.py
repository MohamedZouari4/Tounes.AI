"""
AUDIO GENERATOR MODULE
======================
Enhanced with:
1. Better Streamlit async compatibility
2. Voice selection support
3. Error recovery
4. Audio caching
"""

import asyncio
import os
import tempfile
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Voice mapping for different languages
TTS_VOICES = {
    "en": "en-US-AriaNeural",
    "fr": "fr-FR-DeniseNeural",
    "ar": "ar-TN-ReemNeural"
}

ALTERNATIVE_VOICES = {
    "en": [
        "en-US-GuyNeural",
        "en-GB-SoniaNeural",
        "en-AU-NatashaNeural"
    ],
    "fr": [
        "fr-FR-HenriNeural",
        "fr-CA-SylvieNeural"
    ],
    "ar": [
        "ar-SA-ZariyahNeural",
        "ar-EG-ShakirNeural"
    ]
}


async def _generate_audio_async(text: str, language: str, output_path: str,
                                 voice: str = None) -> tuple:
    """
    Async function to generate audio using Edge TTS.
    
    Args:
        text: Story text to convert
        language: "en", "fr", or "ar"
        output_path: Where to save the MP3 file
        voice: Optional specific voice name override
        
    Returns:
        tuple: (success: bool, error_message: str or None)
    """
    try:
        import edge_tts
        
        selected_voice = voice or TTS_VOICES.get(language, "en-US-AriaNeural")
        communicate = edge_tts.Communicate(text, selected_voice)
        await communicate.save(output_path)
        return True, None
        
    except ImportError:
        return False, "edge-tts not installed. Run: pip install edge-tts"
    except Exception as e:
        return False, f"TTS Error: {str(e)}"


def generate_audio(text: str, language: str = "en", voice: str = None) -> tuple:
    """
    Generate audio narration from text.
    
    Handles async/event loop properly for both standalone and Streamlit contexts.
    
    Args:
        text: Story text to convert to speech
        language: "en", "fr", or "ar"
        voice: Optional specific voice name
        
    Returns:
        tuple: (audio_bytes, error_message)
    """
    try:
        import edge_tts  # Check availability
    except ImportError:
        return None, "edge-tts not installed. Run: pip install edge-tts"
    
    try:
        # Use tempfile for thread safety
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
            output_path = tmp.name
        
        # Handle event loop - compatible with Streamlit's async context
        try:
            loop = asyncio.get_running_loop()
            # We're in an existing async context (Streamlit)
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(_run_async_in_thread, text, language, output_path, voice)
                success, error = future.result(timeout=60)
        except RuntimeError:
            # No running loop - create one
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                success, error = loop.run_until_complete(
                    _generate_audio_async(text, language, output_path, voice)
                )
            finally:
                loop.close()
        
        if not success:
            _cleanup_file(output_path)
            return None, error
        
        # Read the generated audio
        with open(output_path, "rb") as f:
            audio_bytes = f.read()
        
        _cleanup_file(output_path)
        return audio_bytes, None
        
    except Exception as e:
        return None, f"Audio Generation Error: {str(e)}"


def _run_async_in_thread(text, language, output_path, voice):
    """Run async generation in a new thread with its own event loop."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(
            _generate_audio_async(text, language, output_path, voice)
        )
    finally:
        loop.close()


def _cleanup_file(path):
    """Safely remove a temporary file."""
    try:
        if os.path.exists(path):
            os.unlink(path)
    except OSError:
        pass


def get_available_voices(language: str = None) -> dict:
    """Get available voices, optionally filtered by language."""
    if language:
        return {
            "primary": TTS_VOICES.get(language),
            "alternatives": ALTERNATIVE_VOICES.get(language, [])
        }
    return {
        "primary": TTS_VOICES,
        "alternatives": ALTERNATIVE_VOICES
    }


# ============================================
# TEST
# ============================================
if __name__ == "__main__":
    print("🔊 Testing Audio Generator...\n")
    
    test_texts = {
        "en": "Welcome to Carthage, where ancient history comes alive.",
        "fr": "Bienvenue à Carthage, où l'histoire ancienne prend vie.",
        "ar": "مرحباً بك في قرطاج، حيث يحيا التاريخ القديم."
    }
    
    for lang, text in test_texts.items():
        print(f"Testing {lang.upper()}...")
        audio_data, error = generate_audio(text, lang)
        
        if error:
            print(f"  ❌ Error: {error}")
        else:
            output_file = f"test_audio_{lang}.mp3"
            with open(output_file, "wb") as f:
                f.write(audio_data)
            print(f"  ✅ Saved: {output_file} ({len(audio_data)} bytes)")
    
    print("\n🎧 Open the MP3 files to hear the audio!")