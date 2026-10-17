# Enable public video generation
This changes access to the RunPod video generator without exposing the FastAPI token. The public gateway is a separately deployed Cloudflare Worker.

## Setup
1. At Cloudflare Dashboard → Workers & Pages, create a Worker and paste the contents of `public-gateway/worker.js`.
2. Create a **KV namespace** and bind it to this Worker with binding name `LIMITS`.
3. Add Worker **secrets**:
   - `STUDIO_TOKEN` = the current FastAPI private studio token. Never insert it in GitHub.
   - `BACKEND_URL` = `https://ctgj5d89z8v9fs-8000.proxy.runpod.net`.
4. Deploy and copy the URL, e.g., `https://your-video-gateway.workers.dev`.
5. Edit `docs/index.html` and replace `https://REPLACE-WITH-YOUR-PUBLIC-GATEWAY.workers.dev` with your real Worker URL (URL only; no secrets). Commit to GitHub.
6. Ensure ComfyUI and FastAPI are running on RunPod. Public visitors can then submit text-to-video jobs without a token.

## Limits
- 2 submissions per client IP per UTC day (KV best effort; shared IPs may share quota and KV updates are not atomic).
- Public mode only allows text-to-video, ≤ 640×384 and ≤81 frames.
- The backend stays token protected; no RunPod credential is sent to the browser.
- Job listing currently reflects all backend jobs, so **do not treat this as private**. For production, implement per-visitor isolated job storage, signed download links, bot defenses, stronger atomic rate limits, queue caps, and spend limits.
- A user can forge an Origin header; CORS alone is not access control. IP-based limiting is only a basic safeguard.
- Because the GPU has to run and the ComfyUI/FastAPI processes were launched manually, stopping RunPod stops video generation. The Worker cannot render videos itself.
