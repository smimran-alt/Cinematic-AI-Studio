# Cinematic AI Studio

Browser-based cinematic video generation interface hosted on GitHub Pages, designed to connect to a private FastAPI backend and ComfyUI on a rented RunPod GPU.

## GitHub Pages
Settings > Pages > Deploy from branch > main > /docs > Save.

Website: https://smimran-alt.github.io/Cinematic-AI-Studio/

## Architecture
GitHub Pages static frontend -> HTTPS FastAPI API (authenticated with bearer token) -> ComfyUI with compatible text-to-video and image-to-video API workflows -> generated video storage.

## Security
Never put your RunPod API key or backend STUDIO_TOKEN into a public repository. The web frontend asks for a separately issued studio token. Do not expose ComfyUI port 8188 publicly. The initial application is designed for a single owner, not a public multi-user SaaS.

## Important
GitHub Pages cannot execute AI video models. The backend must be deployed separately, with compatible model files and workflows. No rented GPU or running inference service has been provisioned yet. GPU charges apply.

## Backend
The companion Python backend is in the downloadable project archive from the chat. Deploy it on your private GPU server with its requirements, configure STUDIO_TOKEN, ALLOWED_ORIGIN=https://smimran-alt.github.io, COMFYUI_URL, and install the ComfyUI workflows and their model weights. Point the Connect panel at the backend's HTTPS API URL.