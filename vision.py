"""
PART 3: Vision Module - Landmark Identification
================================================
This module handles:
1. Converting uploaded images to base64 format
2. Sending images to Groq Vision API
3. Identifying which Tunisian landmark is in the photo
"""

import base64
import json
from pathlib import Path
from groq import Groq
import os
from dotenv import load_dotenv

load_dotenv()  # Loads the .env file

GROQ_API_KEY = os.getenv("GROQ_API_KEY")



def load_landmarks():
    """Load landmark data from JSON file"""
    data_path = Path(__file__).parent / "landmarks_data.json"
    if data_path.exists():
        with open(data_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None


def encode_image_to_base64(uploaded_file):
    """
    Convert an uploaded image file to base64 string.
    
    Why base64?
    - APIs can't receive raw image files
    - Base64 encodes binary data as text
    - Can be sent in JSON requests
    
    Args:
        uploaded_file: Streamlit UploadedFile object
        
    Returns:
        str: Base64 encoded string of the image
    """
    image_bytes = uploaded_file.getvalue()  # Get raw bytes
    base64_string = base64.b64encode(image_bytes).decode('utf-8')
    return base64_string


def identify_landmark(api_key: str, image_base64: str, image_type: str = "image/jpeg"):
    """
    Use Groq Vision API to identify a Tunisian landmark in an image.
    
    How it works:
    1. Load list of known landmarks
    2. Send image to Llama Vision model
    3. Ask it to identify which landmark it sees
    4. Return the landmark key or "unknown"
    
    Args:
        api_key: Your Groq API key
        image_base64: Base64 encoded image string
        image_type: MIME type (image/jpeg, image/png, etc.)
        
    Returns:
        tuple: (landmark_key, error_message)
               landmark_key is like "carthage", "sidi_bou_said", etc.
               error_message is None if successful
    """
    try:
        # Initialize Groq client
        client = Groq(api_key=GROQ_API_KEY)
        
        # Load our landmark database
        landmarks_data = load_landmarks()
        if not landmarks_data:
            return None, "Could not load landmarks database"
        
        # Create list of landmark names for the AI to choose from
        landmark_names = []
        for key, data in landmarks_data.get("landmarks", {}).items():
            landmark_names.append(f"{data['name']['en']} ({key})")
        
        # Build the prompt for the vision model
        prompt = f"""Analyze this image of a Tunisian landmark.

        Known Tunisian landmarks you can identify:
        {', '.join(landmark_names)}

        Instructions:
        - If you recognize the landmark, respond with ONLY the landmark key
        (e.g., "carthage", "sidi_bou_said", "el_jem_amphitheater")
        - If you cannot identify it, respond with "unknown"
        - Respond with just ONE WORD - the landmark key or "unknown"

        What landmark is this?"""

        # Call Groq Vision API
        response = client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",  # Vision model
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{image_type};base64,{image_base64}"
                            }
                        }
                    ]
                }
            ],
            temperature=0.1,  # Low temperature = more consistent results
            max_tokens=50     # We only need one word
        )
        
        # Extract and clean the response
        result = response.choices[0].message.content.strip().lower()
        result = result.replace('"', '').replace("'", "").strip()
        
        # Validate it's a known landmark
        if result in landmarks_data.get("landmarks", {}):
            return result, None
        else:
            return "unknown", None
            
    except Exception as e:
        return None, f"Vision API Error: {str(e)}"


# ============================================
# TEST THIS MODULE
# ============================================
if __name__ == "__main__":
    """
    Test the vision module standalone.
    
    To test:
    1. Set your API key below
    2. Put a test image in the same folder
    3. Run: python vision.py
    """
    
    # Replace with your actual API key for testing
    TEST_API_KEY = GROQ_API_KEY  # This will be loaded from .env
    
    # Test with a sample image (you need to provide one)
    test_image_path = "test_image.jpg"
    
    if Path(test_image_path).exists():
        with open(test_image_path, "rb") as f:
            image_base64 = base64.b64encode(f.read()).decode('utf-8')
        
        landmark, error = identify_landmark(TEST_API_KEY, image_base64)
        
        if error:
            print(f"❌ Error: {error}")
        else:
            print(f"✅ Identified landmark: {landmark}")
    else:
        print(f"⚠️ Put a test image at: {test_image_path}")