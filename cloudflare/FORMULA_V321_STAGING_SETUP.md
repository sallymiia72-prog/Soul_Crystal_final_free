# V321 protected formula activation — staging only

## Implemented on language-testing
- Cloudflare Worker now records invoice ownership in PAYMENT_SESSIONS (KV) with an HttpOnly claim cookie, verifies Monobank amount/currency/reference/status, and issues an HttpOnly paid-session cookie.
- /api/entitlement/formula checks the server session; /api/private/formula-audio/t0.mp3 (t1, t2) returns audio only with an authenticated formula session.
- The HTML must NOT contain embedded paid MP3 base64. Use V321_PRIVATE_AUDIO_STAGING.html produced from V320; it replaces 3 embedded tracks with private API paths.
- All changes remain un-deployed. Existing public HTML still embeds those tracks.

## Deployment prerequisites (do not deploy until completed)
1. Create a **private** R2 bucket, bind it as FORMULA_PRIVATE, and upload the three extracted tracks with exact keys t0.mp3, t1.mp3, t2.mp3. Never publish them as public static assets or commit them to GitHub.
2. Create a Cloudflare KV namespace and bind it as PAYMENT_SESSIONS. Ensure MONO_TOKEN remains a secret.
3. Upload the modified V321 HTML as index.html in language-testing, configure a staging Cloudflare deployment with these bindings, and run end-to-end browser tests against staging.
4. Confirm the actual Monobank invoice creation, same-browser return, server status check, and session issuance. Browser localStorage must never authorize private audio.
5. Audit and relocate any other premium HTML/JS/audio that should be protected. The current HTML still contains UI and descriptions; client-side hiding is not security.
6. Review other paid products and any certificate/bundle logic; they are not protected by this formula-only change.
7. Verify session expiration, repeated status requests, cookies on mobile browsers, and no unauthorized access to private audio with forged localStorage.
8. Only then consider main deployment after explicit approval.

## Current security boundary
Forging localStorage may reveal player controls, but should NOT fetch protected tracks once private R2 is correctly configured and public embedded copies are removed. This does not protect all premium text and functionality yet.
