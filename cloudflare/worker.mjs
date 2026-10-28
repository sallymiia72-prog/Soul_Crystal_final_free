// Cloudflare build trigger: main branch payment sync 2026-10-03
const MONO_API = "https://api.monobank.ua/api/merchant";

const PRODUCTS = Object.freeze({
  solar: { code: "SOLAR", amount: 50000, name: "Соляр Душі — 12 місяців", displayPrice: "10 €" },
  formula: { code: "FORMULA", amount: 50000, name: "Повне розшифрування 12 енергій / Вібраційний код Душі", displayPrice: "10 €" },
  higher: { code: "HIGHER", amount: 50000, name: "Вище Я — розшифрування та активація", displayPrice: "10 €" },
  geography: { code: "GEOGRAPHY", amount: 25000, name: "Географія Душі — найкраще місце на поточний період", displayPrice: "5 €" },
  soulmate: { code: "SOULMATE", amount: 50000, name: "Призначення союзу / спорідненість душ", displayPrice: "10 €" },
  crystal: { code: "CRYSTAL", amount: 50000, name: "Особистий Кристал Душі — повне розшифрування 12 граней", displayPrice: "10 €" },
  "mandala-image": { code: "MANDALA_IMAGE", amount: 100000, name: "Кристалічна Мандала — PNG / шпалери", displayPrice: "20 €" },
  "mandala-video": { code: "MANDALA_VIDEO", amount: 200000, name: "Жива Кристалічна Мандала зі звучанням", displayPrice: "40 €" },
  "mandala-bundle": { code: "MANDALA_BUNDLE", amount: 250000, name: "Повний комплект Кристалічних Мандал", displayPrice: "50 €" }
});

const PRODUCT_BY_CODE = Object.freeze(
  Object.fromEntries(Object.entries(PRODUCTS).map(([id, product]) => [product.code, { id, ...product }]))
);

function json(body, status = 200, extraHeaders = {}) {
  return Response.json(body, {
    status,
    headers: { "Cache-Control": "no-store", ...extraHeaders }
  });
}

function requestIsSameOrigin(request) {
  const origin = request.headers.get("origin");
  if (!origin) return true;
  try {
    return new URL(origin).host.toLowerCase() === new URL(request.url).host.toLowerCase();
  } catch {
    return false;
  }
}

async function monoRequest(path, token, options = {}) {
  const response = await fetch(`${MONO_API}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      "X-Token": token,
      "X-Cms": "Soul Crystal Store",
      "X-Cms-Version": "1.0",
      ...(options.headers || {})
    }
  });
  const text = await response.text();
  let data = {};
  try {
    data = text ? JSON.parse(text) : {};
  } catch {
    data = { message: text };
  }
  if (!response.ok) {
    const error = new Error(data.errText || data.message || `Monobank HTTP ${response.status}`);
    error.status = response.status;
    throw error;
  }
  return data;
}

async function createInvoice(request, token, env) {
  let body = {};
  try {
    body = await request.json();
  } catch {
    return json({ error: "INVALID_JSON" }, 400);
  }

  const productId = String(body.productId || "");
  const product = PRODUCTS[productId];
  if (!product) return json({ error: "UNKNOWN_PRODUCT" }, 400);

  const reference = `SC_${product.code}_${crypto.randomUUID().replace(/-/g, "")}`;
  const payload = {
    amount: product.amount,
    ccy: 980,
    paymentType: "debit",
    validity: 3600,
    merchantPaymInfo: {
      reference,
      destination: product.name,
      comment: "Soul Crystal Store"
    }
  };

  const invoice = await monoRequest("/invoice/create", token, {
    method: "POST",
    body: JSON.stringify(payload)
  });
  if (!invoice.invoiceId || !invoice.pageUrl) {
    return json({ error: "INVALID_MONO_RESPONSE" }, 502);
  }

  if (!env.PAYMENT_SESSIONS) return json({error:'SESSION_STORAGE_NOT_CONFIGURED'},503);
  const claim = crypto.randomUUID().replace(/-/g,'') + crypto.randomUUID().replace(/-/g,'');
  await env.PAYMENT_SESSIONS.put('invoice:'+invoice.invoiceId, JSON.stringify({claim,productId,reference,amount:product.amount}), {expirationTtl:7200});
  return json({
    invoiceId: invoice.invoiceId,
    pageUrl: invoice.pageUrl,
    productId,
    amount: product.amount,
    currency: "UAH"
  },200,{'Set-Cookie':`sc_invoice_claim=${claim}; Path=/; Secure; HttpOnly; SameSite=Lax; Max-Age=7200`});
}

async function checkInvoice(request, token, env) {
  const invoiceId = String(new URL(request.url).searchParams.get("invoiceId") || "").trim();
  if (!/^[A-Za-z0-9_-]{6,100}$/.test(invoiceId)) {
    return json({ error: "INVALID_INVOICE_ID" }, 400);
  }

  const record = await env.PAYMENT_SESSIONS?.get('invoice:'+invoiceId,{type:'json'});
  const claim = (request.headers.get('Cookie')||'').split(';').map(x=>x.trim()).find(x=>x.startsWith('sc_invoice_claim='))?.split('=')[1];
  if(!record || !claim || record.claim!==claim) return json({error:'INVOICE_NOT_OWNED'},403);
  const invoice = await monoRequest(`/invoice/status?invoiceId=${encodeURIComponent(invoiceId)}`, token, {
    method: "GET"
  });
  const reference = String(invoice.reference || "");
  const product = Object.values(PRODUCT_BY_CODE).find(item => reference.startsWith(`SC_${item.code}_`)) || null;
  const amountMatches = Boolean(product && invoice.ccy === 980 && invoice.amount === product.amount);
  const paid = invoice.status === "success" && amountMatches && product.id===record.productId && invoice.reference===record.reference && invoice.amount===record.amount;
  let extraHeaders={};
  if(paid){const session=crypto.randomUUID().replace(/-/g,'')+crypto.randomUUID().replace(/-/g,'');
    await env.PAYMENT_SESSIONS.put('session:'+session,JSON.stringify({productId:product.id,invoiceId}),{expirationTtl:2592000});
    extraHeaders={'Set-Cookie':`sc_paid_session=${session}; Path=/; Secure; HttpOnly; SameSite=Lax; Max-Age=2592000`};
  }

  return json({
    invoiceId,
    status: invoice.status || "unknown",
    paid,
    productId: paid ? product.id : null
  },200,extraHeaders);
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    if (url.pathname === '/api/entitlement/formula') {
      const c=(request.headers.get('Cookie')||'').split(';').map(x=>x.trim()).find(x=>x.startsWith('sc_paid_session='));
      const session=c&&await env.PAYMENT_SESSIONS?.get('session:'+c.split('=')[1],{type:'json'});
      return json({paid:session?.productId==='formula'});
    }
    if (url.pathname.startsWith('/api/private/formula-audio/')) {
      const c=(request.headers.get('Cookie')||'').split(';').map(x=>x.trim()).find(x=>x.startsWith('sc_paid_session='));
      const session=c&&await env.PAYMENT_SESSIONS?.get('session:'+c.split('=')[1],{type:'json'});
      if(session?.productId!=='formula')return json({error:'PAYMENT_REQUIRED'},403);
      if(!env.FORMULA_PRIVATE)return json({error:'PRIVATE_STORAGE_NOT_CONFIGURED'},503);
      const track=url.pathname.split('/').pop();
      if(!/^t[012]\\.mp3$/.test(track))return json({error:'INVALID_TRACK'},404);
      const obj=await env.FORMULA_PRIVATE.get(track);
      if(!obj)return json({error:'PRIVATE_ASSET_NOT_FOUND'},404);
      return new Response(obj.body,{headers:{'Content-Type':'audio/mpeg','Cache-Control':'private, no-store','Accept-Ranges':'none'}});
    }
    if (url.pathname === '/api/private/formula-activation') {
      const c=(request.headers.get('Cookie')||'').split(';').map(x=>x.trim()).find(x=>x.startsWith('sc_paid_session='));
      const session=c&&await env.PAYMENT_SESSIONS?.get('session:'+c.split('=')[1],{type:'json'});
      if(session?.productId!=='formula')return json({error:'PAYMENT_REQUIRED'},403);
      if(!env.FORMULA_PRIVATE)return json({error:'PRIVATE_STORAGE_NOT_CONFIGURED'},503);
      const obj=await env.FORMULA_PRIVATE.get('formula-activation.html');
      if(!obj)return json({error:'PRIVATE_ASSET_NOT_FOUND'},404);
      return new Response(obj.body,{headers:{'Content-Type':'text/html; charset=utf-8','Cache-Control':'private, no-store'}});
    }
    if (url.pathname !== "/api/payment") return env.ASSETS.fetch(request);
    if (!requestIsSameOrigin(request)) {
      return json({ error: "ORIGIN_NOT_ALLOWED" }, 403);
    }

    const token = env.MONO_TOKEN;
    if (!token) return json({ error: "PAYMENT_NOT_CONFIGURED" }, 503);

    try {
      if (request.method === "POST") return await createInvoice(request, token, env);
      if (request.method === "GET") return await checkInvoice(request, token, env);
      return json({ error: "METHOD_NOT_ALLOWED" }, 405, { Allow: "GET, POST" });
    } catch (error) {
      console.error("Soul Crystal payment error", error);
      const status = error.status >= 400 && error.status < 500 ? error.status : 502;
      return json({ error: "PAYMENT_PROVIDER_ERROR" }, status);
    }
  }
};
