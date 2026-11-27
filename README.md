# Curious Dossier Audio Studio

A simple Streamlit web app for generating narration with Kokoro ONNX.

## Files
- `app.py` — the Studio interface and audio generation
- `requirements.txt` — Python packages Streamlit installs
- `.streamlit/config.toml` — app theme

## Deploy on Streamlit Community Cloud
1. Create a GitHub repository named `curious-dossier-audio-studio`.
2. Upload the contents of this folder to the repository (not the ZIP file itself).
3. Open https://share.streamlit.io/
4. Choose **New app**, select the repository, branch `main`, and file `app.py`.
5. Deploy.

The app downloads the Kokoro INT8 model (~114 MB) and voice file (~27 MB) the first time it starts. It caches them while its hosting environment remains available.

## Important free-hosting limitation
Streamlit Community Cloud is free but has limited CPU and memory and does not provide a dedicated GPU. The app may generate more slowly than the tested Google Colab T4. If it exceeds free resource limits, the reliable solution is a hosted inference service with a free tier or paid compute; this project does not promise unlimited free GPU generation.

Use short scripts for the first test. Do not put private or sensitive scripts into a public app.
