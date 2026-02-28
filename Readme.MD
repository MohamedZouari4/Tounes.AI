# 📖 Tounes.AI — تونس

### AI-Powered Cultural Storytelling Platform for Tunisia

> *Transform Tunisian landmarks into immersive, personalized narrative experiences.*

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.9+-blue?logo=python" alt="Python">
  <img src="https://img.shields.io/badge/Streamlit-1.30+-red?logo=streamlit" alt="Streamlit">
  <img src="https://img.shields.io/badge/Groq-LLM%20%26%20Vision-green" alt="Groq">
  <img src="https://img.shields.io/badge/Languages-AR%20%7C%20FR%20%7C%20EN-orange" alt="Languages">
  <img src="https://img.shields.io/badge/AINC'26-🇹🇳-red" alt="AINC26">
</p>

---

## 🌟 What is Tounes.AI?

**Tounes.AI** (Arabic: تونس — "Tunisia") is an AI-powered platform that transforms static Tunisian landmarks into deeply personal, immersive stories. Instead of reading a Wikipedia article about Carthage, a visitor can upload a photo, choose their preferred storytelling style, and receive a custom narrative — in Arabic, French, or English — where *they* become part of the story.

### The Problem
Traditional tourism information is impersonal, static, and fails to create emotional connections with cultural heritage. Visitors leave historic sites without truly understanding the human stories behind the stones.

### The Solution
Tounes.AI combines **computer vision**, **large language models**, and **multilingual speech synthesis** to:
1. **See** — Identify a landmark from a simple photo
2. **Tell** — Generate a personalized story in the visitor's chosen style and language
3. **Speak** — Deliver the story as natural audio narration

---

## ✨ Features

| Feature | Description |
|---|---|
| 🔍 **Vision AI** | Upload a photo → Tounes.AI identifies the Tunisian landmark using Groq Vision |
| 📖 **6 Story Modes** | Historian, Legend Keeper, Time Traveler, Romantic, Kids Adventure, Movie Director |
| 🌍 **3 Languages** | Arabic (with Tunisian flavor), French, and English |
| 🔊 **Audio Narration** | AI-generated voice narration using Edge TTS (free, high-quality) |
| 👤 **Personalization** | Your name woven into the story + companion context (solo, couple, family, friends) |
| 📊 **Quality Scoring** | Automated story quality metrics (length, language purity, structure) |
| 🔄 **Smart Retries** | Auto-retry with progressively stronger prompts for Arabic quality |
| 🗺️ **Interactive Map** | Visual map of all supported landmarks |
| 🌐 **Full i18n** | Entire UI available in Arabic, French, and English |

---

## 🏛️ Supported Landmarks (8)

| # | Landmark | Region | UNESCO | Era |
|---|---|---|---|---|
| 1 | **Carthage** (قرطاج) | Greater Tunis | ✅ | 814 BC |
| 2 | **Sidi Bou Said** (سيدي بو سعيد) | Greater Tunis | — | 13th century |
| 3 | **Amphitheater of El Jem** (قصر الجم) | Sahel | ✅ | 238 AD |
| 4 | **Dougga** (دقة) | Northern Tunisia | ✅ | 4th century BC |
| 5 | **Medina of Tunis** (المدينة العتيقة) | Tunis | ✅ | 698 AD |
| 6 | **Matmata** (مطماطة) | Southern Tunisia | — | Ancient |
| 7 | **Great Mosque of Kairouan** (جامع عقبة) | Central Tunisia | ✅ | 670 AD |
| 8 | **Tozeur Oasis** (واحة توزر) | Southern Tunisia | — | Ancient |

---

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- A free [Groq API key](https://console.groq.com)

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/MohamedZouari4/Tounes.AI.git
cd tounes-ai

# 2. Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up environment
cp .env.example .env
# Edit .env and add your GROQ_API_KEY

# 5. Run the app
streamlit run app.py
```

The app will open at `http://localhost:8501`.

---

## 📁 Project Structure

```
tounes-ai/
├── app.py                      # Main Streamlit application
├── enhanced_story_generator.py # Story generation with retry & validation
├── story_generator.py          # Backward-compatible story module
├── vision.py                   # Landmark identification (Groq Vision)
├── audio_generator.py          # Text-to-speech (Edge TTS)
├── landmarks_data.json         # Landmark database + UI translations
├── requirements.txt            # Python dependencies
├── .env.example                # Environment variable template
├── .gitignore                  # Git ignore rules
└── README.md                   # This file
```

### Module Responsibilities

| Module | Purpose |
|---|---|
| `app.py` | UI layout, state management, user interaction flow |
| `enhanced_story_generator.py` | Prompt engineering, LLM calls, Arabic validation, quality scoring |
| `vision.py` | Image → landmark identification with confidence scoring |
| `audio_generator.py` | Text → MP3 audio narration |
| `landmarks_data.json` | All landmark data, translations, and UI strings |

---

## 🎭 Story Modes

| Mode | Style | Best For |
|---|---|---|
| 🏛️ **Historian** | Scholarly, factual, rich with dates and names | Learning-focused visitors |
| 👻 **Legend Keeper** | Mystical, mythical, full of folklore | Atmosphere seekers |
| ⚔️ **Time Traveler** | Second-person present tense — you ARE there | Immersive experience lovers |
| 💕 **Romantic** | Poetic, emotional, lyrical | Couples and dreamers |
| 👶 **Kids Adventure** | Simple, fun, exciting, educational | Families with children |
| 🎬 **Movie Director** | Cinematic narration, visual, dramatic | Film and visual storytelling fans |

---

## 🛠️ Technology Stack

| Component | Technology | Why |
|---|---|---|
| **Frontend** | Streamlit | Rapid prototyping, built-in widgets, Python-native |
| **LLM** | Groq (Llama 3.3 70B) | Free tier, fast inference, excellent multilingual |
| **Vision** | Groq (Llama 4 Scout) | Free, multimodal, good accuracy |
| **TTS** | Microsoft Edge TTS | Free, high-quality, supports Tunisian Arabic |
| **Data** | JSON | Simple, portable, no database needed |

---

## 🇹🇳 Arabic Support

Tounes.AI has special handling for Arabic content:
- **Arabic-specific system prompts** to ensure cultural authenticity
- **Post-processing** to remove accidental English artifacts
- **Validation** checking Arabic character ratio (>85%)
- **Auto-retry** with progressively stronger prompts if quality is insufficient
- **RTL layout** with Amiri font for beautiful Arabic rendering
- **Tunisian Arabic TTS voice** (ar-TN-ReemNeural)

---

## 🤝 Contributing

Contributions are welcome! Some ideas:
- Add more landmarks to `landmarks_data.json`
- Create new story modes
- Improve Arabic prompt engineering
- Add more languages (Amazigh, Italian, Spanish)
- Build a mobile-native version
- Add social media sharing

---

## 🙏 Acknowledgments

- **AINC'26** — AI Night Challenges
- **Tunisia's cultural heritage** — The real star of this project

---

<p align="center">
  <strong>صُنع بحب في تونس 🇹🇳</strong><br>
  <em>Made with love in Tunisia</em>
</p>