"""CPU-only scene-template renderer (not generative AI).
Produce MP4 via Pillow + imageio-ffmpeg. Designed for modest laptops."""
import math
import random
import subprocess
from PIL import Image, ImageDraw, ImageFont
import imageio_ffmpeg

def render_cpu(prompt, filename, seed=0, width=640, height=360, frames=60):
    width=max(256,min(854,int(width)//2*2))
    height=max(256,min(480,int(height)//2*2))
    frames=max(12,min(96,int(frames)))
    fps=12
    text=prompt.lower()
    snow=any(word in text for word in ("snow","winter","blizzard","ice","frost"))
    rain=any(word in text for word in ("rain","storm","thunder"))
    space=any(word in text for word in ("space","galaxy","stars","planet"))
    city=any(word in text for word in ("city","building","street","skyscraper"))
    sun=any(word in text for word in ("sun","sunset","sunrise","beach","desert"))
    if not (snow or rain or space or city or sun):
        raise ValueError("CPU Mode supports snow/winter, rain/storm, city, space/stars, or sunset scenes. For arbitrary cinematic prompts, use a generative AI model.")
    rng=random.Random(seed)
    particles=[(rng.random(),rng.random(),rng.uniform(.2,1),rng.randrange(2,5)) for _ in range(90)]
    stars=[(rng.random(),rng.random()*.6,rng.randrange(1,3)) for _ in range(65)]
    font=ImageFont.load_default()
    ffmpeg=imageio_ffmpeg.get_ffmpeg_exe()
    cmd=[ffmpeg,"-y","-loglevel","error","-f","rawvideo","-vcodec","rawvideo","-s",f"{width}x{height}","-pix_fmt","rgb24","-r",str(fps),"-i","-","-an","-vcodec","libx264","-preset","ultrafast","-pix_fmt","yuv420p","-movflags","+faststart",str(filename)]
    proc=subprocess.Popen(cmd,stdin=subprocess.PIPE,stderr=subprocess.PIPE)
    try:
        for frame in range(frames):
            phase=frame/frames
            img=Image.new("RGB",(width,height))
            pixels=ImageDraw.Draw(img)
            top=(11,14,39) if (space or rain or snow) else (34,23,55)
            bottom=(64,56,101) if (space or rain) else (190,111,120)
            for y in range(height):
                t=y/height
                pixels.line((0,y,width,y),fill=tuple(int(top[k]*(1-t)+bottom[k]*t) for k in range(3)))
            if not rain:
                sunx=int(width*.73)
                suny=int(height*.25)
                radius=int(height*.10 if not space else height*.13)
                pixels.ellipse((sunx-radius,suny-radius,sunx+radius,suny+radius),fill=(237,182,137) if not space else (111,103,201))
            if space:
                for x,y,size in stars:
                    px=int(x*width)
                    py=int(y*height)
                    pixels.ellipse((px,py,px+size,py+size),fill=(219,221,249))
            elif city:
                for i in range(12):
                    x=int(i*width/11)
                    h=int(height*(.2+((i*7)%8)*.055))
                    pixels.rectangle((x,height-h,x+int(width/10),height),fill=(20,21,43))
                    for wy in range(height-h+12,height-7,19):
                        for wx in range(x+8,x+int(width/10)-7,15):
                            if (wx+wy+i)%3: pixels.rectangle((wx,wy,wx+3,wy+5),fill=(242,190,131))
            else:
                ground=int(height*.74)
                for j in range(3):
                    offset=j*int(height*.09)
                    pts=[(0,height),(0,ground+offset)]
                    for i in range(9):
                        x=int(i*width/8)
                        peak=ground+offset-int(height*(.14+((i*9+j*5)%6)*.035))
                        pts.extend(((x,peak),(min(width,x+width//16),ground+offset)))
                    pts.append((width,height))
                    pixels.polygon(pts,fill=(16+j*10,21+j*9,40+j*13))
            if snow or rain:
                for x,y,speed,size in particles:
                    py=int(((y+phase*speed*3)%1)*height)
                    px=int(((x+phase*(.13 if snow else -.22)*speed)%1)*width)
                    if rain:
                        pixels.line((px,py,px-3,py+11),fill=(163,181,222),width=1)
                    else:
                        r=max(1,size//2)
                        pixels.ellipse((px-r,py-r,px+r,py+r),fill=(228,235,255))
            pixels.rectangle((0,height-40,width,height),fill=(12,11,26))
            caption=(prompt.strip().replace("\n"," "))[:88]
            pixels.text((14,height-27),caption,fill=(243,234,251),font=font)
            pixels.rectangle((0,height-3,int(width*(frame+1)/frames),height),fill=(166,110,241))
            proc.stdin.write(img.tobytes())
        proc.stdin.close()
        error=proc.stderr.read().decode(errors="replace")
        if proc.wait()!=0: raise RuntimeError("FFmpeg failed: "+error[:300])
    except Exception:
        if proc.stdin and not proc.stdin.closed: proc.stdin.close()
        proc.kill()
        raise
    return str(filename)
