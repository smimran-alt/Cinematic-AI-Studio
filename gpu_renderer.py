"""GPU text-to-video proof of concept using CogVideoX-2B on CUDA.
Install gpu-requirements.txt on an NVIDIA GPU with compatible torch/CUDA.
First run downloads the model to Hugging Face cache; persist HF_HOME under /workspace.
"""
import os
from pathlib import Path

def render_gpu(job, output):
    import torch
    from diffusers import CogVideoXPipeline
    from diffusers.utils import export_to_video

    if not torch.cuda.is_available():
        raise RuntimeError("NVIDIA CUDA GPU not detected by PyTorch")
    model_id = os.environ.get("GPU_VIDEO_MODEL", "THUDM/CogVideoX-2b")
    pipe = CogVideoXPipeline.from_pretrained(model_id, torch_dtype=torch.float16)
    pipe.enable_model_cpu_offload()
    pipe.vae.enable_tiling()
    pipe.vae.enable_slicing()
    try:
        frames = pipe(
            prompt=job["prompt"],
            num_frames=49,
            num_inference_steps=30,
            guidance_scale=6.0,
            generator=torch.Generator(device="cpu").manual_seed(job["seed"])
        ).frames[0]
        output = Path(output)
        output.parent.mkdir(parents=True, exist_ok=True)
        export_to_video(frames, str(output), fps=8)
        return output.name
    finally:
        del pipe
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
