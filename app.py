import os
import re
import subprocess
import tempfile
import urllib.request
from pathlib import Path

import imageio_ffmpeg
import numpy as np
import soundfile as sf
import streamlit as st
from kokoro_onnx import Kokoro

APP_NAME = "Curious Dossier Audio Studio"
MODEL_URL = (
    "https://github.com/thewh1teagle/kokoro-onnx/releases/download/"
    "model-files-v1.1/kokoro-v1.0.int8.onnx"
)
VOICES_URL = (
    "https://github.com/thewh1teagle/kokoro-onnx/releases/download/"
    "model-files-v1.1/voices-v1.0.bin"
)
CACHE_DIR = Path.home() / ".cache" / "curious_dossier_audio_studio"
MODEL_PATH = CACHE_DIR / "kokoro-v1.0.int8.onnx"
VOICES_PATH = CACHE_DIR / "voices-v1.0.bin"

VOICE_CHOICES = [
    "af_heart", "af_bella", "af_nicole", "af_sarah",
    "af_sky", "af_nova", "am_adam", "am_michael",
    "bf_emma", "bf_isabella", "bm_george", "bm_lewis",
]


def download_if_missing(url: str, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.stat().st_size > 1_000_000:
        return

    temporary_path = path.with_suffix(path.suffix + ".part")
    try:
        request = urllib.request.Request(
            url, headers={"User-Agent": "CuriousDossierAudioStudio/1.0"}
        )
        with urllib.request.urlopen(request, timeout=90) as response:
            with open(temporary_path, "wb") as output:
                while True:
                    chunk = response.read(1024 * 1024)
                    if not chunk:
                        break
                    output.write(chunk)
        temporary_path.replace(path)
    finally:
        if temporary_path.exists():
            temporary_path.unlink()


def split_text(text: str, max_chars: int = 420) -> list[str]:
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    chunks = []
    current = ""

    for sentence in sentences:
        sentence = sentence.strip()
        while len(sentence) > max_chars:
            if current:
                chunks.append(current)
                current = ""
            chunks.append(sentence[:max_chars])
            sentence = sentence[max_chars:]
        if not sentence:
            continue
        candidate = (current + " " + sentence).strip()
        if len(candidate) > max_chars and current:
            chunks.append(current)
            current = sentence
        else:
            current = candidate

    if current:
        chunks.append(current)
    return chunks


@st.cache_resource(show_spinner=False)
def load_voice_engine():
    download_if_missing(MODEL_URL, MODEL_PATH)
    download_if_missing(VOICES_URL, VOICES_PATH)
    return Kokoro(str(MODEL_PATH), str(VOICES_PATH))


def make_audio(text: str, voice: str, speed: float):
    engine = load_voice_engine()
    audio_parts = []
    sample_rate = 24000
    pieces = split_text(text)

    progress = st.progress(0, text="Preparing narration...")
    for index, piece in enumerate(pieces, start=1):
        samples, sample_rate = engine.create(
            piece, voice=voice, speed=float(speed), lang="en-us"
        )
        audio_parts.append(np.asarray(samples, dtype=np.float32))
        progress.progress(index / len(pieces), text=f"Generating section {index} of {len(pieces)}...")

    progress.empty()
    audio = np.concatenate(audio_parts)

    with tempfile.TemporaryDirectory() as temp_dir:
        wav_path = Path(temp_dir) / "curious_dossier_narration.wav"
        mp3_path = Path(temp_dir) / "curious_dossier_narration.mp3"
        sf.write(wav_path, audio, sample_rate, subtype="PCM_16")

        ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
        subprocess.run(
            [
                ffmpeg, "-y", "-loglevel", "error", "-i", str(wav_path),
                "-codec:a", "libmp3lame", "-q:a", "2", str(mp3_path)
            ],
            check=True,
            capture_output=True,
        )
        return wav_path.read_bytes(), mp3_path.read_bytes()


st.set_page_config(
    page_title=APP_NAME,
    page_icon="🎙️",
    layout="centered",
)

st.markdown(
    """
    <style>
      .block-container {max-width: 900px; padding-top: 2.2rem; padding-bottom: 3rem;}
      .brand {font-size: 0.78rem; letter-spacing: .22em; font-weight: 700; opacity: .72;}
      .hero {font-size: 2.15rem; font-weight: 800; line-height: 1.12; margin: .25rem 0 .35rem;}
      .sub {opacity: .72; font-size: 1rem; margin-bottom: 1.5rem;}
      div.stButton > button {width: 100%; min-height: 3rem; font-weight: 700;}
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="brand">THE CURIOUS DOSSIER</div>', unsafe_allow_html=True)
st.markdown('<div class="hero">Audio Studio</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub">Turn your narration into natural-sounding audio.</div>',
    unsafe_allow_html=True,
)

with st.container(border=True):
    narration = st.text_area(
        "Your narration",
        height=260,
        placeholder="Paste or type your script here...",
        help="Long scripts are processed in sections.",
    )
    col1, col2 = st.columns(2)
    with col1:
        voice = st.selectbox("Choose a voice", VOICE_CHOICES, index=0)
    with col2:
        speed = st.slider("Speaking speed", 0.75, 1.25, 1.0, 0.05)

    generate = st.button("Generate audio", type="primary")

if generate:
    if not narration.strip():
        st.warning("Please paste your narration first.")
    else:
        try:
            with st.spinner("Loading the voice engine. The first launch may take a few minutes..."):
                wav_bytes, mp3_bytes = make_audio(narration, voice, speed)

            st.success("Your narration is ready.")
            st.audio(mp3_bytes, format="audio/mp3")
            st.download_button(
                "Download MP3",
                data=mp3_bytes,
                file_name="curious_dossier_narration.mp3",
                mime="audio/mpeg",
                type="primary",
            )
            with st.expander("Also download WAV"):
                st.download_button(
                    "Download WAV",
                    data=wav_bytes,
                    file_name="curious_dossier_narration.wav",
                    mime="audio/wav",
                )
        except Exception as error:
            st.error("Audio generation failed.")
            st.caption("Please try a shorter script first. If the problem continues, share the error below.")
            st.code(str(error))

st.caption(
    "First startup downloads the Kokoro INT8 model and voice file. "
    "Free hosting has limited CPU and memory, so generation may be slower than your Colab T4."
)
