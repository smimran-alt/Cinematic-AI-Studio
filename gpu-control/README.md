# GPU Admin Dashboard

The admin dashboard is published at: https://smimran-alt.github.io/Cinematic-AI-Studio/admin.html

The web page is installed in GitHub Pages, but **the Start/Stop buttons will not work until you deploy a separate Cloudflare Worker**. GitHub Pages cannot safely store a RunPod API key, and a control service deployed *on the Pod* would become unreachable after you stop it.

## Deploy

1. Create a Cloudflare account and go to **Workers & Pages → Create → Worker**.
2. Replace the starter Worker code with the contents of `gpu-control/worker.js`, then deploy.
3. In Worker **Settings → Variables and Secrets**, add:
   - Secret `RUNPOD_API_KEY`: your RunPod API key with Pod management permissions.
   - Secret `ADMIN_SECRET`: a new strong, random password (32+ characters, distinct from STUDIO_TOKEN).
   - Variable `POD_ID`: `ctgj5d89z8v9fs`.
4. Open the admin page. Set **GPU Control Service HTTPS URL** to the Worker HTTPS URL (without a trailing slash); enter your **ADMIN_SECRET**, then click **Check GPU status**. Click **Start GPU** or **Stop GPU** when needed.
5. For extra protection, enforce Cloudflare rate limits on Worker requests, and restrict access via Cloudflare Access if available.

### Limits

- The Worker uses the RunPod GraphQL API via bearer authentication and never sends the RunPod API key to browsers.
- The browser's admin secret is entered by the administrator and not stored by the page. Access to the public page itself does not confer control.
- The UI shows the RunPod **desired status**; transitions to RUNNING/EXITED can take time. Check status again.
- Stopping interrupts any active video generation jobs.
- **Starting a Pod will not restart ComfyUI and FastAPI automatically if they were launched manually in terminals.** Configure a persistent startup script or supervisor separately.
- Keep model files on persistent storage. Pod stop may still incur storage charges.
- No public generation/no-login changes are included in this update; that is a separate backend security project.

Official docs: https://docs.runpod.io/sdks/graphql/manage-pods
