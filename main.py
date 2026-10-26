"""Private single-user FastAPI service for the GitHub-hosted Cinematic AI Studio.
Requires an installed ComfyUI model and compatible workflow JSONs."""
import os, json, time, secrets, threading, shutil, subprocess, math
from pathlib import Path
from queue import Queue
import httpx
from fastapi import FastAPI, Header, HTTPException, UploadFile, File, Form, Depends
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

ROOT=Path(__file__).resolve().parent
DATA=ROOT/"data"; OUT=DATA/"videos"; UP=DATA/"uploads"
OUT.mkdir(parents=True,exist_ok=True);UP.mkdir(parents=True,exist_ok=True)
TOKEN=os.environ.get("STUDIO_TOKEN","")
if len(TOKEN)<24: raise RuntimeError("Set STUDIO_TOKEN to a random secret of at least 24 characters")
COMFY=os.environ.get("COMFYUI_URL","http://127.0.0.1:8188").rstrip("/")
ORIGIN=os.environ.get("ALLOWED_ORIGIN","https://smimran-alt.github.io")
app=FastAPI(title="Cinematic AI Studio")
app.add_middleware(CORSMiddleware,allow_origins=[ORIGIN],allow_credentials=False,allow_methods=["GET","POST","DELETE"],allow_headers=["Authorization","Content-Type"])
jobs={}; queue=Queue(); lock=threading.Lock()

def authorized(authorization:str|None=Header(None)):
    if not authorization or not secrets.compare_digest(authorization,"Bearer "+TOKEN):
        raise HTTPException(status_code=401,detail="Invalid studio token")

@app.get("/api/health",dependencies=[Depends(authorized)])
def health():
    try:
        with httpx.Client(timeout=5) as c: r=c.get(COMFY+"/system_stats");r.raise_for_status()
        connected=True
    except Exception: connected=False
    gpu_ready=False; gpu_name=""
    try:
        import torch
        gpu_ready=torch.cuda.is_available()
        if gpu_ready: gpu_name=torch.cuda.get_device_name(0)
    except Exception: pass
    return {"connected":connected,"gpu_ready":gpu_ready,"gpu_name":gpu_name}

@app.get("/api/jobs",dependencies=[Depends(authorized)])
def list_jobs():
    with lock: return sorted([dict(v) for v in jobs.values()],key=lambda x:x["created"],reverse=True)

@app.delete("/api/jobs/completed",dependencies=[Depends(authorized)])
def clear_finished_jobs():
    """Delete completed/failed job history and local media; preserve active jobs."""
    removed=[]
    with lock:
        for ident, record in list(jobs.items()):
            if record.get("status") in ("completed", "failed"):
                removed.append(record)
                del jobs[ident]
    for record in removed:
        file_name=record.get("filename")
        if file_name and Path(file_name).name==file_name:
            (OUT/file_name).unlink(missing_ok=True)
        image_path=record.get("image_path")
        if image_path:
            p=Path(image_path)
            if p.parent.resolve()==UP.resolve():
                p.unlink(missing_ok=True)
    return {"deleted": len(removed)}

@app.post("/api/jobs",dependencies=[Depends(authorized)])
async def submit(mode:str=Form("text"),prompt:str=Form(...),negative:str=Form(""),
    width:int=Form(832),height:int=Form(480),frames:int=Form(81),duration:int|None=Form(None),seed:int|None=Form(None),
    image:UploadFile|None=File(None)):
    if mode not in ("text","image","hf","cpu","gpu") or not 3<=len(prompt)<=5000: raise HTTPException(422,"Invalid mode or prompt")
    if not (256<=width<=1920 and 256<=height<=1080 and 9<=frames<=241):raise HTTPException(422,"Invalid dimensions or frames")
    if duration is not None and duration not in (5,10,20,30): raise HTTPException(422,"Duration must be 5, 10, 20 or 30 seconds")
    if duration is not None and mode!="text": raise HTTPException(422,"Duration mode currently supports text-to-video only")
    ident=secrets.token_hex(12); image_path=None
    if mode=="image":
        if image is None or image.content_type not in ("image/jpeg","image/png","image/webp"):raise HTTPException(422,"PNG, JPEG or WebP image required")
        extension={"image/jpeg":".jpg","image/png":".png","image/webp":".webp"}[image.content_type]
        image_path=UP/(ident+extension)
        content=await image.read(15*1024*1024+1)
        if len(content)>15*1024*1024:raise HTTPException(413,"Image too large")
        image_path.write_bytes(content)
    record={"id":ident,"mode":mode,"prompt":prompt,"negative":negative,"width":width,"height":height,"frames":frames,
            "seed":seed if seed is not None else secrets.randbelow(2147483647),"image_path":str(image_path) if image_path else None,
            "status":"queued","filename":None,"error":None,"created":time.time(),"duration":duration,"progress":0}
    with lock:jobs[ident]=record
    queue.put(ident)
    return {"id":ident,"status":"queued"}

@app.get("/videos/{name}",dependencies=[Depends(authorized)])
def video(name:str):
    if Path(name).name!=name or not (OUT/name).is_file():raise HTTPException(404,"Video not found")
    return FileResponse(OUT/name,media_type="video/mp4",filename=name)

def replace_values(v,mapping):
    if isinstance(v,dict):return {k:replace_values(x,mapping) for k,x in v.items()}
    if isinstance(v,list):return [replace_values(x,mapping) for x in v]
    if isinstance(v,str) and v in mapping:return mapping[v]
    if isinstance(v,str):
        for key,val in mapping.items():v=v.replace(key,str(val))
    return v

def render_movie(job):
    """Produce a timed MP4 from sequential ~5-second Wan clips."""
    import imageio_ffmpeg
    ffmpeg=imageio_ffmpeg.get_ffmpeg_exe()
    seconds=job["duration"]
    clips=math.ceil(seconds / (81 / 16))
    segments=[]
    try:
        for i in range(clips):
            with lock:
                if job["id"] in jobs: jobs[job["id"]]["progress"]=i
            part=dict(job, id=f'{job["id"]}_part{i+1}', duration=None, frames=81,
                      seed=(job["seed"]+i) % 2147483647)
            filename=render(part)
            source=OUT/filename
            if source.suffix.lower() not in (".mp4",".webm",".gif"):
                raise RuntimeError("Unsupported clip type")
            segments.append(source)
        final=OUT/(job["id"]+".mp4")
        # Re-encode in one continuous output, normalize timestamps and match requested duration.
        args=[ffmpeg,"-hide_banner","-loglevel","error","-y"]
        for source in segments: args.extend(["-i",str(source)])
        inputs="".join(f"[{i}:v:0]setpts=PTS-STARTPTS,fps=16,scale={job['width']}:{job['height']}:flags=lanczos,setsar=1[v{i}];" for i in range(len(segments)))
        concat="".join(f"[v{i}]" for i in range(len(segments)))+f"concat=n={len(segments)}:v=1:a=0[outv]"
        args.extend(["-filter_complex",inputs+concat,"-map","[outv]","-t",str(seconds),
                     "-c:v","libx264","-pix_fmt","yuv420p","-crf","19","-preset","veryfast",
                     "-movflags","+faststart",str(final)])
        completed=subprocess.run(args,capture_output=True,text=True,timeout=900)
        if completed.returncode!=0:
            raise RuntimeError("MP4 joining failed: "+completed.stderr[-400:])
        return final.name
    finally:
        for source in segments: source.unlink(missing_ok=True)

def render(job):
    if job.get("duration") and job["mode"]=="text": return render_movie(job)
    if job["mode"] == "gpu":
        from gpu_renderer import render_gpu
        return render_gpu(job, OUT/(job["id"]+".mp4"))
    if job["mode"] == "cpu":
        from cpu_renderer import render_cpu
        filename=job["id"]+".mp4"
        render_cpu(job["prompt"],OUT/filename,job["seed"],job["width"],job["height"],job["frames"])
        return filename

    if job["mode"] == "hf":
        hf_token=os.environ.get("HF_TOKEN","")
        if not hf_token:
            raise RuntimeError("HF_TOKEN is not configured on your private backend")
        from huggingface_hub import InferenceClient
        model=os.environ.get("HF_VIDEO_MODEL","Wan-AI/Wan2.2-TI2V-5B")
        provider=os.environ.get("HF_VIDEO_PROVIDER","fal-ai")
        result=InferenceClient(provider=provider,api_key=hf_token,timeout=900).text_to_video(
            job["prompt"],model=model)
        if not isinstance(result,bytes):
            raise RuntimeError("Hugging Face did not return video bytes")
        filename=job["id"]+".mp4"
        (OUT/filename).write_bytes(result)
        return filename

    workflow=ROOT/"workflows"/(job["mode"]+".json")
    if not workflow.exists():raise RuntimeError("Missing ComfyUI API workflow: "+str(workflow))
    mapping={"__PROMPT__":job["prompt"],"__NEGATIVE__":job["negative"],"__WIDTH__":job["width"],
        "__HEIGHT__":job["height"],"__FRAMES__":job["frames"],"__SEED__":job["seed"],"__IMAGE__":""}
    with httpx.Client(timeout=120) as client:
        if job["image_path"]:
            with open(job["image_path"],"rb") as f:
                response=client.post(COMFY+"/upload/image",files={"image":(Path(job["image_path"]).name,f)})
            response.raise_for_status();mapping["__IMAGE__"]=response.json()["name"]
        payload=replace_values(json.loads(workflow.read_text(encoding="utf-8")),mapping)
        response=client.post(COMFY+"/prompt",json={"prompt":payload,"client_id":"cinematic-ai-studio"})
        response.raise_for_status();prompt_id=response.json()["prompt_id"]
        deadline=time.time()+3600
        while time.time()<deadline:
            response=client.get(COMFY+"/history/"+prompt_id,timeout=30);response.raise_for_status()
            entry=response.json().get(prompt_id)
            if entry:
                if entry.get("status",{}).get("status_str")=="error":raise RuntimeError("ComfyUI workflow execution failed")
                for node in entry.get("outputs",{}).values():
                    for key in ("gifs","videos","images"):
                        for artifact in node.get(key,[]):
                            name=artifact.get("filename","")
                            if name.lower().endswith((".mp4",".webm",".gif")):
                                media=client.get(COMFY+"/view",params={"filename":name,"subfolder":artifact.get("subfolder",""),"type":artifact.get("type","output")},timeout=180)
                                media.raise_for_status()
                                ext=Path(name).suffix.lower();dest=OUT/(job["id"]+ext)
                                dest.write_bytes(media.content)
                                return dest.name
                if entry.get("status",{}).get("completed"):raise RuntimeError("Workflow completed without a supported video output")
            time.sleep(4)
        raise TimeoutError("Generation exceeded one hour")

def worker():
    while True:
        ident=queue.get()
        try:
            with lock:jobs[ident]["status"]="running";snapshot=dict(jobs[ident])
            result=render(snapshot)
            with lock:jobs[ident]["filename"]=result;jobs[ident]["status"]="completed"
        except Exception as exc:
            with lock:jobs[ident]["error"]=str(exc)[:500];jobs[ident]["status"]="failed"
        finally:queue.task_done()

@app.on_event("startup")
def start_worker():threading.Thread(target=worker,daemon=True).start()
