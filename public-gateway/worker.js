// Cinematic AI Studio public video gateway for Cloudflare Workers.
// Secrets: STUDIO_TOKEN (private FastAPI token), BACKEND_URL (RunPod HTTPS origin).
// KV namespace binding: LIMITS (for best-effort daily per-IP limits).
const PAGE_ORIGIN="https://smimran-alt.github.io";
const json=(obj,status=200)=>new Response(JSON.stringify(obj),{status,headers:{"content-type":"application/json","cache-control":"no-store"}});
const cors=(response,origin)=>{const h=new Headers(response.headers);if(origin===PAGE_ORIGIN){h.set("access-control-allow-origin",origin);h.set("vary","Origin");h.set("access-control-expose-headers","content-disposition");}return new Response(response.body,{status:response.status,headers:h});};
export default {async fetch(request,env){
const origin=request.headers.get("origin")||"";
if(request.method==="OPTIONS")return new Response(null,{status:204,headers:{"access-control-allow-origin":PAGE_ORIGIN,"access-control-allow-methods":"GET, POST, OPTIONS","access-control-allow-headers":"Content-Type","access-control-max-age":"3600"}});
if(origin!==PAGE_ORIGIN)return json({detail:"Origin not permitted"},403);
if(!env.STUDIO_TOKEN||!env.BACKEND_URL||!env.LIMITS)return cors(json({detail:"Public gateway not configured"},503),origin);
const path=new URL(request.url).pathname;
if(!["/api/health","/api/jobs"].includes(path)&&!/^\/videos\/[a-f0-9]{24}\.(mp4|webm|gif)$/.test(path))return cors(json({detail:"Not found"},404),origin);
if(path==="/api/jobs"&&request.method==="POST"){
const type=request.headers.get("content-type")||"";
if(!type.startsWith("multipart/form-data"))return cors(json({detail:"Expected form data"},415),origin);
const n=Number(request.headers.get("content-length")||"0");if(n>25000)return cors(json({detail:"Request too large"},413),origin);
let form;try{form=await request.formData()}catch{return cors(json({detail:"Invalid form data"},400),origin)}
if(form.get("mode")!=="text")return cors(json({detail:"Public mode currently supports text-to-video only"},422),origin);
const prompt=String(form.get("prompt")||"").trim(),width=Number(form.get("width")||512),height=Number(form.get("height")||288),frames=Number(form.get("frames")||33);
if(prompt.length<3||prompt.length>1500||width>640||height>384||width<256||height<256||frames>81||frames<9)return cors(json({detail:"Public limit: up to 640×384 and 81 frames; prompt 3–1500 characters"},422),origin);
const ip=request.headers.get("cf-connecting-ip")||"anonymous";const key="daily:"+new Date().toISOString().slice(0,10)+":"+ip;
const hits=Number(await env.LIMITS.get(key)||"0");if(hits>=2)return cors(json({detail:"Daily limit reached: two videos per visitor"},429),origin);
const updated=new FormData();for(const field of ["mode","prompt","negative","width","height","frames","seed"]){const v=form.get(field);if(v!==null&&typeof v==="string")updated.set(field,v)}updated.set("mode","text");updated.set("width",String(width));updated.set("height",String(height));updated.set("frames",String(frames));
const backend=String(env.BACKEND_URL).replace(/\/$/,"");
try{const res=await fetch(backend+path,{method:"POST",headers:{Authorization:"Bearer "+env.STUDIO_TOKEN},body:updated});const data=await res.text();if(res.ok)await env.LIMITS.put(key,String(hits+1),{expirationTtl:86400});return cors(new Response(data,{status:res.status,headers:{"content-type":"application/json","cache-control":"no-store"}}),origin)}catch{return cors(json({detail:"GPU backend unavailable"},503),origin)}
}
if(request.method!=="GET")return cors(json({detail:"Method not allowed"},405),origin);
try{const url=String(env.BACKEND_URL).replace(/\/$/,"")+path;const res=await fetch(url,{headers:{Authorization:"Bearer "+env.STUDIO_TOKEN}});const headers=new Headers();headers.set("cache-control","no-store");headers.set("content-type",res.headers.get("content-type")||"application/octet-stream");if(res.headers.has("content-disposition"))headers.set("content-disposition",res.headers.get("content-disposition"));return cors(new Response(res.body,{status:res.status,headers}),origin)}catch{return cors(json({detail:"GPU backend unavailable"},503),origin)}
}};
