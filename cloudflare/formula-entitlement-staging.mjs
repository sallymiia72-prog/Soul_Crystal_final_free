// Experimental server-side formula entitlement for language-testing.
// Requires Cloudflare KV binding PAYMENT_SESSIONS and private media storage.
// Never deploy until the paid player/assets have been removed from public HTML.
const SESSION_COOKIE="sc_formula_session";
const json=(data,status=200,headers={})=>Response.json(data,{status,headers:{"Cache-Control":"no-store",...headers}});
const cookieValue=(req,name)=>req.headers.get("Cookie")?.split(";").map(x=>x.trim()).find(x=>x.startsWith(name+"="))?.slice(name.length+1)||"";
const randomToken=()=>Array.from(crypto.getRandomValues(new Uint8Array(32)),x=>x.toString(16).padStart(2,"0")).join("");
const secureCookie=(value)=>`${SESSION_COOKIE}=${value}; Path=/; HttpOnly; Secure; SameSite=Lax; Max-Age=2592000`;
export async function createFormulaSession(request,env){
  if(!env.PAYMENT_SESSIONS||!env.MONO_TOKEN)return json({error:"NOT_CONFIGURED"},503);
  const origin=request.headers.get("Origin");
  if(origin&&new URL(origin).origin!==new URL(request.url).origin)return json({error:"BAD_ORIGIN"},403);
  const invoiceId=String((await request.json().catch(()=>({}))).invoiceId||"");
  const claim=cookieValue(request,"sc_invoice_claim");
  if(!/^[A-Za-z0-9_-]{6,100}$/.test(invoiceId)||!claim)return json({error:"MISSING_INVOICE"},400);
  // Invoice creation must previously store a random browser-bound claim under this key.
  const record=await env.PAYMENT_SESSIONS.get("invoice:"+invoiceId,{type:"json"});
  if(!record||record.claim!==claim||record.productId!=="formula")return json({error:"NOT_OWNER"},403);
  const resp=await fetch("https://api.monobank.ua/api/merchant/invoice/status?invoiceId="+encodeURIComponent(invoiceId),{headers:{"X-Token":env.MONO_TOKEN}});
  if(!resp.ok)return json({error:"MONO_UNAVAILABLE"},502);
  const status=await resp.json();
  if(status.status!=="success"||status.ccy!==980||status.amount!==50000||!String(status.reference||"").startsWith("SC_FORMULA_"))return json({error:"NOT_PAID"},403);
  const token=randomToken();
  await env.PAYMENT_SESSIONS.put("session:"+token,JSON.stringify({productId:"formula",invoiceId}),{expirationTtl:2592000});
  return json({paid:true,productId:"formula"},200,{"Set-Cookie":secureCookie(token)});
}
export async function formulaEntitlement(request,env){
  const token=cookieValue(request,SESSION_COOKIE);
  if(!token||!env.PAYMENT_SESSIONS)return json({paid:false},200);
  const session=await env.PAYMENT_SESSIONS.get("session:"+token,{type:"json"});
  return json({paid:session?.productId==="formula"});
}
export async function serveFormulaProtectedAsset(request,env,key){
  const token=cookieValue(request,SESSION_COOKIE);
  const session=token&&await env.PAYMENT_SESSIONS?.get("session:"+token,{type:"json"});
  if(session?.productId!=="formula")return json({error:"PAYMENT_REQUIRED"},403);
  // R2 bucket FORMULA_PRIVATE must be PRIVATE, not accessible via public asset paths.
  if(!env.FORMULA_PRIVATE)return json({error:"PRIVATE_ASSETS_NOT_CONFIGURED"},503);
  const asset=await env.FORMULA_PRIVATE.get(key);
  if(!asset)return json({error:"NOT_FOUND"},404);
  return new Response(asset.body,{headers:{"Content-Type":asset.httpMetadata?.contentType||"application/octet-stream","Cache-Control":"private, no-store","X-Content-Type-Options":"nosniff"}});
}
