# NVIDIA RTX 5090 deployment — Cinematic AI Studio

## Status
**Preparation only.** This repository does not rent or start GPU Pods and does not contain pretrained video model weights. You must activate your own RunPod Pod and choose and test compatible video workflows.

## Recommended hardware
- RunPod GPU Pod: **NVIDIA RTX 5090, 32 GB VRAM**
- Official RunPod template: **ComfyUI - CUDA 13** (template ID `2lv7ev3wfp`, verify template in console)
- Disk: size according to model; budget ~100 GB or more of persistent workspace for video checkpoints and outputs.
- Control costs: review hourly rate before deployment; set spending limits or Pod termination guard where available; stop and terminate Pods appropriately. Stopped Pods may incur storage charges.

## Architecture
GitHub Pages static frontend -> your authenticated HTTPS FastAPI backend -> private ComfyUI on the GPU Pod -> MP4 download through FastAPI.

The official RunPod ComfyUI template autostarts on port 8188, but its default port 8188 HTTP proxy is **public and unauthenticated**. **Do not publish or share the ComfyUI proxy URL.** Prefer an environment without a public 8188 mapping, or use a private tunnel and put an authenticated proxy in front before exposing any service. The public FastAPI endpoint must use a strong token and HTTPS. You may need a custom Pod template/network configuration to avoid exposing 8188.

## Step 1 — Provision the GPU
1. Sign in: https://www.runpod.io/console/pods
2. Select Community or Secure Cloud availability, choose RTX 5090, and inspect actual price.
3. Select official **ComfyUI - CUDA 13** template.
4. Check exposed ports and disable public ComfyUI access if configuring a custom template; expose only the authenticated API port via HTTPS if using a single Pod.
5. Attach persistent storage for model files and outputs, verify charges, and deploy.

## Step 2 — Load a real video model
RunPod's ComfyUI template does not automatically provide a video model. Select an RTX 5090-compatible workflow (for example, a memory-optimized Wan family model) and install its:
- model checkpoint(s) and text encoders
- required VAE, custom nodes, and workflow dependencies
- correct text-to-video and image-to-video **API-format** ComfyUI workflow JSON

Export working ComfyUI workflows as `workflows/text.json` and `workflows/image.json` under this repository's backend deployment. Replace the relevant workflow values using placeholder markers described in `workflows/README.md`:
`__PROMPT__`, `__NEGATIVE__`, `__WIDTH__`, `__HEIGHT__`, `__FRAMES__`, `__SEED__`, `__IMAGE__`.
The selected workflow MUST export a playable MP4/WebM/GIF artifact in ComfyUI history. MP4 is recommended for cross-device playback.

## Step 3 — Deploy the authenticated backend
From the cloned repository on the GPU Pod (Python 3.11+):
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export STUDIO_TOKEN="$(python -c 'import secrets; print(secrets.token_urlsafe(36))')"
export ALLOWED_ORIGIN="https://smimran-alt.github.io"
export COMFYUI_URL="http://127.0.0.1:8188"
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```
Place FastAPI behind a **secured HTTPS reverse proxy** on an HTTPS address you control, OR an authenticated secure tunnel with proper access controls. Configure the proxy to pass `Authorization` headers. A public FastAPI endpoint is only suitable for personal use with a high-entropy token and budget controls; the current project does not implement multi-user accounts, production rate limiting, or persistent job tracking.

Never add `STUDIO_TOKEN`, RunPod API keys, or Hugging Face secrets to a public GitHub repository.

## Step 4 — Connect the frontend
1. Visit https://smimran-alt.github.io/Cinematic-AI-Studio/
2. Paste your **FastAPI backend's HTTPS URL** in **Backend HTTPS address**. This is NOT your ComfyUI 8188 URL.
3. Paste the private `STUDIO_TOKEN` value in **Private studio token**.
4. Click **Connect**. When ComfyUI is reachable by the backend, it should show GPU online.

## Step 5 — Generate the first clip
Prompt: `Snow falling gently over a realistic pine forest at dusk, a slow cinematic tracking camera, detailed atmosphere, natural lighting.`
- Start small with dimensions and frame count required by the model's workflow (for example 832x480 and 49–81 frames where supported).
- Submit **Text to video** and watch the **Generation queue**.
- Preview and download the finished video.

## Frequent problems
- **404 or no frontend**: GitHub Pages setting must publish `main /docs`.
- **401 Invalid token**: the frontend private token and backend `STUDIO_TOKEN` must match.
- **GPU offline**: FastAPI cannot reach ComfyUI; verify `COMFYUI_URL` from within the backend.
- **Missing workflow**: install/test ComfyUI video workflow and save the API-format JSON in `workflows/`.
- **Workflow completed without video**: configure a compatible video-combine/export node that emits a recorded video artifact.
- **Out of memory**: select a smaller/quantized model, reduce frames/resolution, or use a higher-VRAM GPU.
- **Download fails**: verify that the workflow saved a valid video file and the backend can access ComfyUI's output API.

## Sources
- Official ComfyUI template: https://github.com/runpod/runpod-plugins-official/blob/main/plugins/runpod/skills/runpod-templates/reference/comfyui.md
- Official RTX 5090 CUDA 13 instructions: https://github.com/runpod/runpod-plugins-official/blob/main/plugins/runpod/skills/runpod/golden-paths/02-comfyui-pod/variant-b-prebuilt.md
