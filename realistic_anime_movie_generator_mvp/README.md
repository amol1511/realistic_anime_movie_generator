# Realistic AI Anime Movie Generator (MVP)

This is an MVP slideshow-style **AI Movie Generator** that converts a short story into a narrated animated slideshow (images + narration).

## Features (MVP)
- Splits the story into several scenes
- Generates images for each scene using the Hugging Face Inference API (Stable Diffusion XL)
- Synthesizes narration for each scene using gTTS
- Stitches images + narration into an MP4 using MoviePy
- Streamlit UI for input and preview

## Setup & Deploy

1. Create a new repository and add these files or upload the ZIP content to your Streamlit app folder.
2. Add a Hugging Face API token (required) into Streamlit Secrets with key `HF_TOKEN` and optionally set `HF_SDXL_URL` if you use a custom endpoint.

Example `secrets.toml`:
```toml
HF_TOKEN = "your_hf_token_here"
HF_SDXL_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"
```

3. Install requirements and run locally:
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Notes & Limitations
- Using HF Hosted inference may consume credits and has rate limits.
- This MVP creates a slideshow video — for real frame-by-frame animation consider integrating AnimateDiff or Runway for motion generation.
- Replace gTTS with ElevenLabs for more realistic voices.
