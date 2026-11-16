HERITAGE FIXED-COPY PATCH — 16 Nov 2026
======================================

WHAT THIS FIXES (from your 3 screenshots)
1. The scary "cannot identify image file <_io.BytesIO object at 0x...>" banner:
   the backend no longer leaks Pillow's raw error into the page. You get a
   clean message instead, and phone HEIC photos now decode too (after the
   pip install step below).
2. Stale old verdict + broken photo staying on screen after a failed upload:
   a failed verify now goes back to the clean upload screen.
3. Museum photo shown as "NON-HERITAGE" rejection while the text said
   "Unknown Heritage Specimen": a low-confidence Gemini "not heritage" call
   can no longer override the Tier-1 verdict, and when Gemini does reject
   confidently, the message now says so in Gemini's own words. NOTE: that
   museum is NOT in the 101-site catalogue, so "Unknown" (not a verified
   match) is still the correct outcome for it.
4. Gemini describing the White House but giving no answer: the Tier-2
   prompt now requires the identity field to match the site named in its
   evidence, and requires naming a clearly identifiable out-of-catalogue
   site. The "ADJUDICATION" badge also no longer shows when Tier 2 never ran.

HOW TO APPLY (on your laptop, in the fixed-copy folder)
1. Close the backend terminal (Ctrl+C in the uvicorn window) if it is running.
2. Unzip this file INTO the fixed-copy project folder, overwriting the
   8 files + FIXES_APPLIED.md when asked. Keep the folder structure.
3. In the backend venv, install the one new dependency:
     .venv\Scripts\python.exe -m pip install -r requirements.txt
   (run from the project root; this adds pillow-heif for HEIC photos.)
4. Start the backend again exactly as before (uvicorn). The frontend
   (Vite dev server on 5175) picks up the changes automatically — just
   refresh the page. If you run a built frontend, run `npm run build` again.

RETEST (please send screenshots of these two)
1. White House photo again -> expect "Proposed identity (unverified):
   White House" with the OUT-OF-CATALOG badge. If it still shows the plain
   "Unknown heritage specimen" view, expand TELEMETRY and screenshot the
   Tier-2 section so I can see exactly what Gemini returned.
2. Museum photo again -> expect the "Unknown heritage specimen" view
   (NOT the red NON-HERITAGE rejection), unless Gemini confidently says
   it is not a heritage structure — in that case the message will now say
   so explicitly.
3. Upload any unreadable/corrupt file -> clean error message + upload
   screen, no stale verdict underneath.

NOT IN THIS PATCH (unchanged on purpose)
- Thresholds 0.75 / 0.08: untouched.
- FAISS index: still the old 577-vector build. Jama Masjid + the 17 new
  anchors only become searchable after the FIXES_APPLIED.md section 4
  rebuild. That is a separate step — say the word and I will walk you
  through it.
- Nothing here touches GitHub. This patch is for your local fixed copy only.
