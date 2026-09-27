const MONO_API = "https://api.monobank.ua/api/merchant";

const PRODUCTS = Object.freeze({
  solar: { code: "SOLAR", amount: 50000, name: "Соляр Душі — 12 періодів" },
  formula: { code: "FORMULA", amount: 50000, name: "Повна Формула Душі" },
  higher: { code: "HIGHER", amount: 50000, name: "Розшифрування Вищого Я" },
  crystal: { code: "CRYSTAL", amount: 50000, name: "Особистий Кристал Душі" },
  soulmate: { code: "SOULMATE", amount: 50000, name: "Призначення союзу" },
  "mandala-image": { code: "MANDALA_IMAGE", amount: 100000, name: "Кристалічна Мандала — зображення" },
  "mandala-video": { code: "MANDALA_VIDEO", amount: 200000, name: "Жива Кристалічна Мандала" },
  "mandala-bundle": { code: "MANDALA_BUNDLE", amount: 250000, name: "Повний комплект Кристалічних Мандал" },
  certificate: { code: "CERTIFICATE", amount: 150000, name: "Свідоцтво про народження Душі" }
});

const PRODUCT_BY_CODE = Object.freeze(
  Object.fromEntries(Object.entries(PRODUCTS).map(([id, product]) => [product.code, { id, ...product }]))
);

function json(body, status = 200) {
  return Response.json(body, {
    status,
    headers: { "Cache-Control": "no-store" }
  });
}

function requestIsSameOrigin(request) {
  const origin = request.headers.get("origin");
  if (!origin) return true;
  try { return new URL(origin).host.toLowerCase() === new URL(request.url).host.toLowerCase(); }
  catch { return false; }
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
  try { data = text ? JSON.parse(text) : {}; } catch { data = { message: text }; }
  if (!response.ok) {
    const error = new Error(data.errText || data.message || `Monobank HTTP ${response.status}`);
    error.status = response.status;
    throw error;
  }
  return data;
}

async function createInvoice(request, token) {
  let body = {};
  try { body = await request.json(); } catch { return json({ error: "INVALID_JSON" }, 400); }
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
  if (!invoice.invoiceId || !invoice.pageUrl) return json({ error: "INVALID_MONO_RESPONSE" }, 502);

  return json({
    invoiceId: invoice.invoiceId,
    pageUrl: invoice.pageUrl,
    productId,
    amount: product.amount,
    currency: "UAH"
  });
}

async function checkInvoice(request, token) {
  const invoiceId = String(new URL(request.url).searchParams.get("invoiceId") || "").trim();
  if (!/^[A-Za-z0-9_-]{6,100}$/.test(invoiceId)) return json({ error: "INVALID_INVOICE_ID" }, 400);

  const invoice = await monoRequest(`/invoice/status?invoiceId=${encodeURIComponent(invoiceId)}`, token, {
    method: "GET"
  });
  const match = /^SC_([A-Z0-9_]+)_/.exec(String(invoice.reference || ""));
  const product = match ? PRODUCT_BY_CODE[match[1]] : null;
  const amountMatches = Boolean(product && invoice.ccy === 980 && invoice.amount === product.amount);
  const paid = invoice.status === "success" && amountMatches;

  return json({
    invoiceId,
    status: invoice.status || "unknown",
    paid,
    productId: amountMatches ? product.id : null
  });
}

export default {
  async fetch(request) {
    if (!requestIsSameOrigin(request)) return json({ error: "ORIGIN_NOT_ALLOWED" }, 403);
    const token = process.env.MONO_TOKEN;
    if (!token) return json({ error: "PAYMENT_NOT_CONFIGURED" }, 503);

    try {
      if (request.method === "POST") return await createInvoice(request, token);
      if (request.method === "GET") return await checkInvoice(request, token);
      return new Response(JSON.stringify({ error: "METHOD_NOT_ALLOWED" }), {
        status: 405,
        headers: { "Content-Type": "application/json; charset=utf-8", "Cache-Control": "no-store", Allow: "GET, POST" }
      });
    } catch (error) {
      console.error("Soul Crystal payment error", error);
      const status = error.status >= 400 && error.status < 500 ? error.status : 502;
      return json({ error: "PAYMENT_PROVIDER_ERROR" }, status);
    }
  }
};
