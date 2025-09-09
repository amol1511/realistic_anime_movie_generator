import streamlit as st
import requests
import io
import tempfile
import os
from gtts import gTTS
from PIL import Image
from moviepy.editor import ImageClip, concatenate_videoclips, AudioFileClip

st.set_page_config(page_title="Realistic AI Anime Movie Generator (MVP)", page_icon="🎬", layout="centered")
st.title("🎬 Realistic AI Anime Movie Generator (MVP)")
st.write("Enter a short story and generate a short animated slideshow-styled movie (images + narration).")
st.markdown("""**Notes:** This app uses the Hugging Face Inference API (Stable Diffusion XL) to generate images.

- You must add a `HF_TOKEN` in Streamlit secrets or a `.env` file.
- Generating images may cost inference credits on Hugging Face depending on the model and usage.""")

HF_API_URL = st.secrets.get(
    "HF_SDXL_URL",
    "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"
)
HF_TOKEN = st.secrets.get("HF_TOKEN", "")


def generate_image_via_hf(prompt):
    headers = {"Authorization": f"Bearer {HF_TOKEN}"} if HF_TOKEN else {}
    payload = {"inputs": prompt}
    resp = requests.post(HF_API_URL, headers=headers, json=payload, stream=True, timeout=120)
    if resp.status_code != 200:
        raise Exception(f"Image generation failed: {resp.status_code} - {resp.text}")
    return resp.content


def synthesize_narration(text, lang="en"):
    tts = gTTS(text, lang=lang)
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
    tts.write_to_fp(tmp)
    tmp.flush()
    tmp.close()
    return tmp.name


def make_video(image_bytes_list, audio_paths, out_path="movie.mp4", image_duration=4):
    clips = []
    temp_image_paths = []
    for img_bytes in image_bytes_list:
        img_temp = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
        img_temp.write(img_bytes)
        img_temp.flush()
        img_temp.close()
        temp_image_paths.append(img_temp.name)

    for img_path, audio_path in zip(temp_image_paths, audio_paths):
        clip = ImageClip(img_path).set_duration(image_duration)
        audio = AudioFileClip(audio_path)
        clip = clip.set_audio(audio)
        clips.append(clip)

    if not clips:
        raise Exception("No clips to combine.")

    final = concatenate_videoclips(clips, method="compose")
    final.write_videofile(out_path, fps=24, codec="libx264", audio_codec="aac")
    for p in temp_image_paths:
        try:
            os.remove(p)
        except:
            pass
    return out_path


with st.form("movie_form"):
    story = st.text_area("Enter a short story (2-6 sentences):", height=180)
    scenes_count = st.slider("Number of scenes (images)", 1, 6, 3)
    image_style = st.selectbox(
        "Style hint (affects prompts)",
        ["vibrant realistic anime", "cinematic anime", "soft watercolor anime", "dark cyberpunk anime"]
    )
    submitted = st.form_submit_button("🎥 Generate Movie")

if submitted:
    if not HF_TOKEN:
        st.error("Hugging Face API token is required. Add HF_TOKEN in Streamlit secrets.")
    elif not story.strip():
        st.warning("Please enter a story.")
    else:
        st.info("Splitting story into scenes and generating assets...")
        import re

        sentences = re.split(r"(?<=[.!?])\s+", story.strip())
        n = scenes_count
        scenes = [""] * n
        for i, s in enumerate(sentences):
            scenes[i % n] += (" " + s).strip()

        images = []
        audio_files = []
        failed = False
        for idx, scene in enumerate(scenes):
            if not scene.strip():
                scene = sentences[min(idx, len(sentences) - 1)] if sentences else "A scenic shot."
            prompt = f"{image_style}, highly detailed, cinematic lighting, 4k, {scene}"
            try:
                img_bytes = generate_image_via_hf(prompt)
                images.append(img_bytes)
            except Exception as e:
                st.error(f"Image generation failed for scene {idx+1}: {e}")
                failed = True
                break
            try:
                audio_path = synthesize_narration(scene)
                audio_files.append(audio_path)
            except Exception as e:
                st.error(f"Audio synthesis failed for scene {idx+1}: {e}")
                failed = True
                break

        if not failed and images and audio_files:
            st.info("Rendering final video...")
            try:
                out = make_video(images, audio_files, out_path="anime_movie.mp4", image_duration=4)
                st.success("✅ Movie generated!")
                st.video(out)
                with open(out, "rb") as f:
                    st.download_button("⬇️ Download Movie", f, file_name="anime_movie.mp4", mime="video/mp4")
            except Exception as e:
                st.error(f"Video rendering failed: {e}")
        for p in audio_files:
            try:
                os.remove(p)
            except:
                pass
