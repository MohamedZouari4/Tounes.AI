"""
VISION MODULE - Landmark Identification
========================================
Enhanced with:
1. Confidence scoring and detailed analysis
2. Better error handling with user-friendly messages
3. Support for more image formats
4. Fuzzy matching for landmark identification
5. Graceful fallbacks
"""

import base64
import json
import re
from pathlib import Path
from groq import Groq
import os
from dotenv import load_dotenv

load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")


def load_landmarks():
    """Load landmark data from JSON file."""
    data_path = Path(__file__).parent / "landmarks_data.json"
    if data_path.exists():
        with open(data_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None


def encode_image_to_base64(uploaded_file) -> str:
    """
    Convert an uploaded image file to base64 string.
    
    Args:
        uploaded_file: Streamlit UploadedFile object or file-like object
        
    Returns:
        str: Base64 encoded string of the image
    """
    if hasattr(uploaded_file, 'getvalue'):
        image_bytes = uploaded_file.getvalue()
    elif hasattr(uploaded_file, 'read'):
        image_bytes = uploaded_file.read()
    else:
        image_bytes = uploaded_file
    
    return base64.b64encode(image_bytes).decode('utf-8')


# Fuzzy matching map: common variations → canonical key
LANDMARK_ALIASES = {
    "carthage": "carthage",
    "cartagena": "carthage",
    "carthago": "carthage",
    "قرطاج": "carthage",
    "sidi bou said": "sidi_bou_said",
    "sidi_bou_said": "sidi_bou_said",
    "sidi bou": "sidi_bou_said",
    "سيدي بو سعيد": "sidi_bou_said",
    "el jem": "el_jem_amphitheater",
    "el_jem": "el_jem_amphitheater",
    "el_jem_amphitheater": "el_jem_amphitheater",
    "el djem": "el_jem_amphitheater",
    "amphitheater": "el_jem_amphitheater",
    "colosseum": "el_jem_amphitheater",
    "coliseum": "el_jem_amphitheater",
    "قصر الجم": "el_jem_amphitheater",
    "الجم": "el_jem_amphitheater",
    "dougga": "dougga",
    "thugga": "dougga",
    "دقة": "dougga",
    "medina": "medina_tunis",
    "medina_tunis": "medina_tunis",
    "medina tunis": "medina_tunis",
    "المدينة العتيقة": "medina_tunis",
    "zitouna": "medina_tunis",
    "matmata": "matmata",
    "troglodyte": "matmata",
    "star wars": "matmata",
    "مطماطة": "matmata",
    "kairouan": "kairouan",
    "القيروان": "kairouan",
    "great mosque": "kairouan",
    "uqba": "kairouan",
    "عقبة": "kairouan",
    "tozeur": "tozeur",
    "توزر": "tozeur",
    "oasis": "tozeur",
    "chott": "tozeur",
}


def _fuzzy_match_landmark(text: str, landmarks_data: dict) -> str:
    """
    Try to match a text response to a known landmark key.
    Uses exact match first, then fuzzy matching.
    
    Args:
        text: The vision model's response text
        landmarks_data: The landmarks database
        
    Returns:
        str: Matched landmark key or "unknown"
    """
    text_clean = text.strip().lower().replace('"', '').replace("'", "")
    
    # Direct key match
    if text_clean in landmarks_data.get("landmarks", {}):
        return text_clean
    
    # Alias match
    for alias, key in LANDMARK_ALIASES.items():
        if alias in text_clean:
            if key in landmarks_data.get("landmarks", {}):
                return key
    
    # Partial match against landmark names
    for key, data in landmarks_data.get("landmarks", {}).items():
        for lang_name in data.get("name", {}).values():
            if lang_name.lower() in text_clean or text_clean in lang_name.lower():
                return key
    
    return "unknown"


def identify_landmark(api_key: str, image_base64: str, 
                      image_type: str = "image/jpeg") -> tuple:
    """
    Use Groq Vision API to identify a Tunisian landmark in an image.
    
    Returns:
        tuple: (landmark_key, confidence_info, error_message)
               landmark_key: e.g. "carthage", "sidi_bou_said", or "unknown"
               confidence_info: dict with details about the identification
               error_message: None if successful
    """
    try:
        client = Groq(api_key=api_key or GROQ_API_KEY)
        
        landmarks_data = load_landmarks()
        if not landmarks_data:
            return None, None, "Could not load landmarks database"
        
        # Build concise landmark reference
        landmark_ref = []
        for key, data in landmarks_data.get("landmarks", {}).items():
            keywords = ", ".join(data.get("keywords", [])[:4])
            landmark_ref.append(
                f"- {data['name']['en']} (key: {key}) — {keywords}"
            )
        
        prompt = f"""You are an expert on Tunisian landmarks and architecture. Analyze this image carefully.

Known Tunisian landmarks:
{chr(10).join(landmark_ref)}

Instructions:
1. Identify which landmark is shown in the image
2. Respond in this EXACT format:
   LANDMARK: <landmark_key>
   CONFIDENCE: <high/medium/low>
   REASON: <brief explanation>

If you cannot identify the landmark, respond:
   LANDMARK: unknown
   CONFIDENCE: low
   REASON: <what you see in the image>

Analyze the image now:"""

        response = client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:{image_type};base64,{image_base64}"}
                    }
                ]
            }],
            temperature=0.1,
            max_tokens=200
        )
        
        result_text = response.choices[0].message.content.strip()
        
        # Parse structured response
        confidence_info = _parse_vision_response(result_text)
        
        # Try to match landmark
        landmark_key = _fuzzy_match_landmark(
            confidence_info.get("raw_landmark", result_text), 
            landmarks_data
        )
        
        confidence_info["matched_key"] = landmark_key
        
        return landmark_key, confidence_info, None
        
    except Exception as e:
        error_msg = str(e)
        if "rate_limit" in error_msg.lower() or "429" in error_msg:
            return None, None, "Rate limit reached. Please wait a moment and try again."
        elif "invalid_api_key" in error_msg.lower() or "401" in error_msg:
            return None, None, "Invalid API key. Please check your Groq API key."
        elif "model" in error_msg.lower():
            return None, None, "Vision model unavailable. Please try again later."
        else:
            return None, None, f"Vision API Error: {error_msg}"


def _parse_vision_response(text: str) -> dict:
    """Parse the structured vision response into a dict."""
    info = {
        "raw_response": text,
        "raw_landmark": "",
        "confidence": "low",
        "reason": ""
    }
    
    # Try to extract structured fields
    landmark_match = re.search(r'LANDMARK:\s*(.+)', text, re.IGNORECASE)
    confidence_match = re.search(r'CONFIDENCE:\s*(\w+)', text, re.IGNORECASE)
    reason_match = re.search(r'REASON:\s*(.+)', text, re.IGNORECASE)
    
    if landmark_match:
        info["raw_landmark"] = landmark_match.group(1).strip()
    else:
        # Fallback: use the whole text
        info["raw_landmark"] = text.split('\n')[0].strip()
    
    if confidence_match:
        info["confidence"] = confidence_match.group(1).strip().lower()
    
    if reason_match:
        info["reason"] = reason_match.group(1).strip()
    
    return info


# ============================================
# TEST
# ============================================
if __name__ == "__main__":
    print("🔍 Testing Vision Module...\n")
    
    test_image_path = "test_image.jpg"
    
    if Path(test_image_path).exists():
        with open(test_image_path, "rb") as f:
            image_base64 = base64.b64encode(f.read()).decode('utf-8')
        
        landmark, confidence, error = identify_landmark(GROQ_API_KEY, image_base64)
        
        if error:
            print(f"❌ Error: {error}")
        else:
            print(f"✅ Identified: {landmark}")
            print(f"   Confidence: {confidence.get('confidence', 'N/A')}")
            print(f"   Reason: {confidence.get('reason', 'N/A')}")
    else:
        print(f"⚠️  Put a test image at: {test_image_path}")