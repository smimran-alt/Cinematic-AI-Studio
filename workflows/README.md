# ComfyUI workflows

Export two workflows in **API format** from ComfyUI:
- `workflows/text.json` for text-to-video
- `workflows/image.json` for image-to-video

Use placeholders in the exported JSON values wherever applicable:
`__PROMPT__`, `__NEGATIVE__`, `__SEED__`, `__WIDTH__`, `__HEIGHT__`, `__FRAMES__`, and `__IMAGE__`.

Your video model, loader nodes, checkpoints and output nodes must be installed separately. A successful workflow must produce a video in ComfyUI history. Workflow files are intentionally ignored by git because they depend on which model you install. Never assume every ComfyUI model supports the same nodes or settings.