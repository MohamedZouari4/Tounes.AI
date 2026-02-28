"""
PART 5: Audio Generator Module
==============================
This module handles:
1. Converting story text to spoken audio
2. Supporting multiple languages (EN, FR, AR)
3. Using Edge TTS (completely FREE, no API key!)

Edge TTS is Microsoft's text-to-speech service.
It's free, high-quality, and has many voices including Tunisian Arabic!
"""

import asyncio
from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file
GROQ_API_KEY = os.getenv("GROQ_API_KEY") 


# Voice mapping for different languages
# These are Microsoft Edge TTS voice names
TTS_VOICES = {
    "en": "en-US-AriaNeural",      # American English - Female, natural
    "fr": "fr-FR-DeniseNeural",    # French - Female, natural
    "ar": "ar-TN-ReemNeural"       # Tunisian Arabic - Female! (This is special!)
}

# Alternative voices you can use:
ALTERNATIVE_VOICES = {
    "en": [
        "en-US-GuyNeural",         # American English - Male
        "en-GB-SoniaNeural",       # British English - Female
        "en-AU-NatashaNeural"      # Australian English - Female
    ],
    "fr": [
        "fr-FR-HenriNeural",       # French - Male
        "fr-CA-SylvieNeural"       # Canadian French - Female
    ],
    "ar": [
        "ar-SA-ZariyahNeural",     # Saudi Arabic - Female
        "ar-EG-ShakirNeural"       # Egyptian Arabic - Male
    ]
}


async def generate_audio_async(text: str, language: str, output_path: str):
    """
    Async function to generate audio using Edge TTS.
    
    Why async?
    - Edge TTS uses async/await pattern
    - Allows non-blocking operation
    - Better for web apps
    
    Args:
        text: The story text to convert to speech
        language: "en", "fr", or "ar"
        output_path: Where to save the MP3 file
        
    Returns:
        tuple: (success: bool, error_message: str or None)
    """
    try:
        import edge_tts
        
        # Get the appropriate voice for the language
        voice = TTS_VOICES.get(language, "en-US-AriaNeural")
        
        # Create the TTS communication object
        communicate = edge_tts.Communicate(text, voice)
        
        # Save to file
        await communicate.save(output_path)
        
        return True, None
        
    except ImportError:
        return False, "edge-tts not installed. Run: pip install edge-tts"
    except Exception as e:
        return False, f"TTS Error: {str(e)}"


def generate_audio(text: str, language: str = "en"):
    """
    Main function to generate audio (handles async for you).
    
    This is the function you call from your app.
    
    Args:
        text: Story text to convert to speech
        language: "en", "fr", or "ar"
        
    Returns:
        tuple: (audio_bytes, error_message)
               audio_bytes is the MP3 data you can play
               error_message is None if successful
    """
    try:
        import edge_tts  # Check if installed
        
        # Create temporary output path
        output_path = "story_audio.mp3"
        
        # Run the async function
        # This creates an event loop and runs our async function
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        success, error = loop.run_until_complete(
            generate_audio_async(text, language, output_path)
        )
        
        loop.close()
        
        if not success:
            return None, error
        
        # Read the generated audio file
        with open(output_path, "rb") as f:
            audio_bytes = f.read()
        
        return audio_bytes, None
        
    except ImportError:
        return None, "edge-tts not installed. Run: pip install edge-tts"
    except Exception as e:
        return None, f"Audio Generation Error: {str(e)}"


def get_available_voices(language: str = None):
    """
    Get list of available voices.
    
    Useful for letting users choose their preferred voice.
    
    Args:
        language: Filter by language code, or None for all
        
    Returns:
        dict: Available voices
    """
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
# TEST THIS MODULE
# ============================================
if __name__ == "__main__":
    """
    Test the audio generator standalone.
    
    To test:
    1. Make sure edge-tts is installed: pip install edge-tts
    2. Run: python audio_generator.py
    3. Check for output file: test_audio.mp3
    """
    
    print("🔊 Testing Audio Generator...\n")
    
    # Test texts in different languages
    test_texts = {
        "en": "Welcome to Carthage, where ancient history comes alive. You stand where Hannibal once stood, gazing across the Mediterranean.",
        "fr": "Bienvenue à Carthage, où l'histoire ancienne prend vie. Vous vous tenez là où Hannibal se tenait autrefois.",
        "ar": "مرحباً بك في قرطاج، حيث يحيا التاريخ القديم. أنت تقف حيث وقف حنبعل ذات يوم."
    }
    
    for lang, text in test_texts.items():
        print(f"Testing {lang.upper()}...")
        
        # Generate audio
        audio_data, error = generate_audio(text, lang)
        
        if error:
            print(f"  ❌ Error: {error}")
        else:
            # Save test file
            output_file = f"test_audio_{lang}.mp3"
            with open(output_file, "wb") as f:
                f.write(audio_data)
            print(f"  ✅ Saved: {output_file}")
    
    print("\n🎧 Open the MP3 files to hear the audio!")