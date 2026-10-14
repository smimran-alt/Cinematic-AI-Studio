# Local CPU text-to-video setup — Windows

This version renders actual MP4 videos using **your laptop CPU**, with Pillow and a bundled FFmpeg executable. It does **not** generate photorealistic AI footage or interpret arbitrary text. Supported scenes: `snow`, `winter`, `rain`, `storm`, `city`, `buildings`, `space`, `stars`, `sunset`, `sunrise`, `beach` and `desert`. The scene and animation style are templates; the prompt appears as a caption.

## 1. Install Python and get the code

Install **Python 3.12** from python.org (check 'Add python.exe to PATH') and Git for Windows.

Open **Windows PowerShell**:

```powershell
git clone https://github.com/smimran-alt/Cinematic-AI-Studio.git
cd Cinematic-AI-Studio
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

If PowerShell blocks activation, use `.venv\Scripts\python.exe` for the following commands instead of activating the environment.

## 2. Configure your secret

Still in PowerShell, generate your own random token:

```powershell
$env:STUDIO_TOKEN = (python -c "import secrets; print(secrets.token_urlsafe(32))")
$env:ALLOWED_ORIGIN = "https://smimran-alt.github.io"
```

**Keep this terminal open and do not publish or screenshot the token.** You will need to copy the value of `STUDIO_TOKEN` privately into your browser's Private studio token field.

## 3. Start the CPU video backend

```powershell
python -m uvicorn main:app --host 127.0.0.1 --port 8000
```

Open http://127.0.0.1:8000/docs in your laptop's browser to see the API documentation (API methods require authentication).

Your GitHub Pages website is HTTPS, so to connect it reliably to your local server, use a **secure HTTPS tunnel**. Never forward port 8000 from your router, and never expose ComfyUI port 8188.

## 4. Create a temporary HTTPS address using Cloudflare Tunnel

Install [cloudflared](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/) on Windows.

In a **second PowerShell window**, run:

```powershell
cloudflared tunnel --url http://127.0.0.1:8000
```

cloudflared will print a temporary URL like `https://random-words.trycloudflare.com`. Your URL will be different.

**Security:** This temporary URL is reachable from the internet. The backend requires your strong private bearer token, so do not share either the token or link publicly. Quick Tunnels are intended for testing, not production. Close the tunnel window when finished.

## 5. Connect your existing GitHub website

1. Visit https://smimran-alt.github.io/Cinematic-AI-Studio/
2. In Backend HTTPS address, paste the HTTPS tunnel URL.
3. In Private studio token, paste the private value from your PowerShell session.
4. Click Connect. The status might show "GPU offline" because no ComfyUI GPU is installed — **this is expected for CPU Mode**.
5. Scroll to **Create a new clip** and type `Snow falling over mountains at night`.
6. Scroll to **Local CPU Text-to-Video** and click **Create MP4 using my laptop CPU**.
7. In **Generation queue**, wait until your job says `completed`.
8. Click **Preview & download** and download the MP4.

**Tip:** Start at width=640, height=360, frames=60. 60 frames at 12 FPS = about 5 seconds. The renderer limits dimensions to 854x480 and output to 96 frames to keep laptop CPU demands reasonable. Frame rate is fixed at 12 FPS. The job queue is in memory and resets when the backend restarts.

## Troubleshooting

- `Invalid studio token`: check the token value. Do not paste your GitHub or Hugging Face passwords.
- `API unavailable`: make sure BOTH PowerShell windows are still running, and confirm the tunnel address.
- `Unsupported scene`: include one of the scene keywords listed at the top of this document.
- `Memory high`: close heavy background programs before running videos.
- `GPU offline`: expected for CPU-only mode; submit a CPU job anyway.
- The generation engine needs both the **laptop backend** and the **GitHub frontend**. GitHub Pages alone cannot use your processor while your laptop is off.

## What comes next

Once a CPU clip works, we can add more templates (ocean, forest, fire), image animation, voice overlays, transitions and longer clips. Generative AI text-to-video requires a compatible model and much stronger compute.
