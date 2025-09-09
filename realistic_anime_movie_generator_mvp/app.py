import streamlit as st
import requests
import tempfile
import os
import re
from gtts import gTTS
from moviepy.editor import ImageClip, concatenate_videoclips, AudioFileClip

# =========================
# CONFIGURATION
# =========================
st.set_page_config(page_title="Realistic AI Anime Movie Generator", page_icon="🎬", layout="centered")
st.title("🎬 Realistic AI Anime Movie Generator")
st.write("Turn a short story into a mini movie with AI-generated images & narration!")

# Hugging Face API
HF_API_URL = st.secrets.get(
    "HF_SDXL_URL",
    "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"
)
HF_TOKEN = st.secrets.get("HF_TOKEN", "")

# =========================
# HELPER FUNCTIONS
# =========================
def generate_image(prompt: str) -> bytes:
    """Call Hugging Face API for image generation"""
    headers = {"Authorization": f"Bearer {HF_TOKEN}"} if HF_TOKEN else {}
    payload = {"inputs": prompt}

    try:
        resp = requests.post(HF_API_URL, headers=headers, json=payload, timeout=120)
        resp.raise_for_status()
        return resp.content
    except Exception as e:
        raise RuntimeError(f"Image generation failed: {e}")

def synthesize_audio(text: str, lang="en") -> str:
    """Convert text to speech and return audio file path"""
    tts = gTTS(text, lang=lang)
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
    tts.save(tmp.name)
    return tmp.name

def create_movie(images: list, audios: list, output_path="movie.mp4", duration=4) -> str:
    """Combine images and audio into a movie"""
    clips = []
    for img_path, audio_path in zip(images, audios):
        clip = ImageClip(img_path).set_duration(duration)
        clip = clip.set_audio(AudioFileClip(audio_path))
        clips.append(clip)

    final = concatenate_videoclips(clips, method="compose")
    final.write_videofile(output_path, fps=24, codec="libx264", audio_codec="aac", verbose=False, logger=None)
    return output_path

# =========================
# UI FORM
# =========================
with st.form("movie_form"):
    story = st.text_area("📖 Enter a short story (2-6 sentences):", height=180)
    scenes_count = st.slider("🎞️ Number of scenes", 1, 6, 3)
    style = st.selectbox("🎨 Style", ["vibrant realistic anime", "cinematic anime", "watercolor", "cyberpunk"])
    submit = st.form_submit_button("🎥 Generate Movie")

# =========================
# MAIN LOGIC
# =========================
if submit:
    if not HF_TOKEN:
        st.error("⚠️ Missing Hugging Face Token! Add `HF_TOKEN` in Streamlit secrets.")
    elif not story.strip():
        st.warning("Please enter a story.")
    else:
        st.info("⏳ Processing your story...")

        # Split story into scenes
        sentences = re.split(r"(?<=[.!?])\s+", story.strip())
        scenes = [""] * scenes_count
        for i, s in enumerate(sentences):
            scenes[i % scenes_count] += (" " + s).strip()

        img_files, audio_files = [], []
        failed = False

        for idx, text in enumerate(scenes):
            prompt = f"{style}, cinematic lighting, 4k, highly detailed, {text}"
            try:
                img_bytes = generate_image(prompt)
                img_file = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
                img_file.write(img_bytes)
                img_file.flush()
                img_files.append(img_file.name)

                audio_path = synthesize_audio(text)
                audio_files.append(audio_path)
            except Exception as e:
                st.error(f"❌ Error generating scene {idx+1}: {e}")
                failed = True
                break

        if not failed and img_files and audio_files:
            try:
                st.info("🎞️ Rendering movie...")
                movie_path = create_movie(img_files, audio_files)
                st.success("✅ Movie generated!")
                st.video(movie_path)
                with open(movie_path, "rb") as f:
                    st.download_button("⬇️ Download Movie", f, file_name="anime_movie.mp4", mime="video/mp4")
            except Exception as e:
                st.error(f"❌ Video rendering failed: {e}")

        # Cleanup
        for path in img_files + audio_files:
            try:
                os.remove(path)
            except:
                pass
