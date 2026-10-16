# GPU Video Generator — Quick Start (RunPod or any NVIDIA CUDA VM)

The live page is **https://smimran-alt.github.io/Cinematic-AI-Studio/generate.html**.
GitHub Pages is STATIC and cannot run the model. GPU inference runs in a separately started Python backend on the GPU VM.

## 1. Create or connect to a running NVIDIA GPU

Use an NVIDIA CUDA-capable GPU (RTX 3090 / 4090 suggested). Use an image with a functioning CUDA-enabled PyTorch installation and JupyterLab with token/password authentication. Never expose unauthenticated JupyterLab or raw ComfyUI. Check the GPU is actually attached:

```bash
python -c "import torch; print(torch.cuda.is_available(),torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'No GPU')"
```

Do not proceed if False. Stop the Pod if you cannot connect to the GPU; retain the Pod for provider troubleshooting rather than terminating if logs are needed.

## 2. In the GPU JupyterLab terminal

```bash
cd /workspace
git clone https://github.com/smimran-alt/Cinematic-AI-Studio.git
cd Cinematic-AI-Studio
python -m pip install -r requirements.txt -r gpu-requirements.txt
```

Prefer a persistent network volume mounted at /workspace; otherwise the model cache and output videos may be erased when the container resets. The first render downloads CogVideoX-2b weights from Hugging Face. Ensure enough storage (40 GB may not suffice with all dependencies and cached downloads).

## 3. Start the authenticated API (internal port 8000)

```bash
export HF_HOME=/workspace/hf-cache
export STUDIO_TOKEN="$(python -c 'import secrets; print(secrets.token_urlsafe(36))')"
echo "Copy and privately save your STUDIO_TOKEN: $STUDIO_TOKEN"
python -m uvicorn main:app --host 127.0.0.1 --port 8000
```

Keep this terminal running. Opening port 8000 directly to the internet is NOT recommended. Use a separate managed HTTPS reverse proxy / tunnel that forwards HTTPS requests to localhost:8000, with access controls. Ensure the HTTPS hostname is unique to your server; do not paste API secrets in public issue comments or source code.

If using the GitHub Pages frontend, the backend must be public HTTPS, not localhost, not the JupyterLab login URL, and not a raw 8188 ComfyUI endpoint. The API enforces STUDIO_TOKEN and CORS restricted to https://smimran-alt.github.io. Keep the token private.

## 4. Connect from the frontend

Open https://smimran-alt.github.io/Cinematic-AI-Studio/generate.html.

- Backend HTTPS URL = public HTTPS hostname of your secured backend, e.g. https://gpu-api.example.com (example only).
- Studio token = STUDIO_TOKEN set above (do not commit it).
- Click Connect to GPU. When it reports GPU connected, enter prompt and click Generate video.
- The queue polls for completion and securely downloads the MP4 through /videos/{filename}.

**The backend is NOT deployed automatically by pushing this GitHub repository.** To finish the connection you must have an actual live GPU Pod and an HTTPS forwarding address. The video page cannot use a RunPod JupyterLab :8888 URL as an API backend.

## How it works

- Browser submits `POST /api/jobs` with mode=gpu and the prompt.
- GPU backend queues the job and loads CogVideoX-2b, generates 49 frames at 8fps, and saves MP4.
- Browser polls `GET /api/jobs`; preview/download uses authenticated `GET /videos/{filename}`.
- GPU video rendering is a proof of concept. The model may need dependency/memory tuning on a specific GPU; no end-to-end run has yet been verified.

## Cost controls

GPU costs accrue while a Pod is running, including while idle or downloading models. Stop the GPU if initialization fails or when done. Storage charges may continue. Do not store valuable work only in ephemeral container disk.
