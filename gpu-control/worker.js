// Deploy as a Cloudflare Worker outside RunPod. Configure secrets RUNPOD_API_KEY and ADMIN_SECRET,
// and variable POD_ID=ctgj5d89z8v9fs. Never put these secrets in the HTML.
const ORIGIN="https://smimran-alt.github.io";
function json(data,status=200,origin=""){return new Response(JSON.stringify(data),{status,headers:{"Content-Type":"application/json","Cache-Control":"no-store",...(origin===ORIGIN?{"Access-Control-Allow-Origin":ORIGIN,"Vary":"Origin"}:{})}})}
async function sameSecret(a,b){const enc=new TextEncoder();const [x,y]=await Promise.all([crypto.subtle.digest("SHA-256",enc.encode(a)),crypto.subtle.digest("SHA-256",enc.encode(b))]);const v=new Uint8Array(x),w=new Uint8Array(y);let mismatch=0;for(let i=0;i<v.length;i++)mismatch|=v[i]^w[i];return mismatch===0;}
export default {async fetch(request,env){const origin=request.headers.get("Origin")||"";if(origin!==ORIGIN)return json({error:"Origin not allowed"},403);
if(request.method==="OPTIONS")return new Response(null,{status:204,headers:{"Access-Control-Allow-Origin":ORIGIN,"Access-Control-Allow-Methods":"GET, POST, OPTIONS","Access-Control-Allow-Headers":"Authorization, Content-Type","Access-Control-Max-Age":"600","Vary":"Origin"}});
if(!env.RUNPOD_API_KEY||!env.ADMIN_SECRET||!env.POD_ID)return json({error:"Control service not configured"},503,origin);
const auth=request.headers.get("Authorization")||"";if(!auth.startsWith("Bearer ")||!(await sameSecret(auth.slice(7),env.ADMIN_SECRET)))return json({error:"Unauthorized"},401,origin);
const {pathname}=new URL(request.url);let gql,op;
if(pathname==="/status"&&request.method==="GET"){op="pod";gql="query($podId:String!){pod(input:{podId:$podId}){id name desiredStatus runtime{uptimeInSeconds}}}"}
else if(pathname==="/action"&&request.method==="POST"){let body;try{body=await request.json()}catch{return json({error:"Invalid JSON"},400,origin)}
if(body.action==="start"){op="podResume";gql="mutation($podId:String!){podResume(input:{podId:$podId,gpuCount:1}){id name desiredStatus}}"}
else if(body.action==="stop"){op="podStop";gql="mutation($podId:String!){podStop(input:{podId:$podId}){id name desiredStatus}}"}
else return json({error:"Unsupported action"},400,origin);
}else return json({error:"Not found"},404,origin);
try{const upstream=await fetch("https://api.runpod.io/graphql",{method:"POST",headers:{"Content-Type":"application/json","Authorization":"Bearer "+env.RUNPOD_API_KEY},body:JSON.stringify({query:gql,variables:{podId:env.POD_ID}})});const result=await upstream.json();if(!upstream.ok||result.errors||!result.data?.[op])return json({error:"RunPod request failed",details:result.errors?.map(x=>x.message).slice(0,2)},502,origin);const pod=result.data[op];return json({status:pod.desiredStatus||(pod.runtime?"RUNNING":"UNKNOWN"),name:pod.name||"",id:pod.id},200,origin)}catch{return json({error:"Unable to contact RunPod"},502,origin)}
}}};
