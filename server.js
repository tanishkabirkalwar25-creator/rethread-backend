// RE-THREAD production API. Env: PORT, AI_SERVICE_URL (Python service), ALLOWED_ORIGIN (your frontend URL).
const express = require("express"), cors = require("cors");
const app = express(), AI = (process.env.AI_SERVICE_URL || "").replace(/\/$/, "");
app.use(cors({ origin: process.env.ALLOWED_ORIGIN || true }));
app.use(express.json({ limit: "20mb" }));
app.get("/api/health", (_q, res) => res.json({ success: true, service: "rethread-backend", status: "running" }));
const OK = /^data:image\/(jpeg|png|webp);base64,[A-Za-z0-9+/=]+$/;
app.post("/api/analyze-image", async (req, res) => {
  const im = (req.body && req.body.images) || {};
  if (!im.full || !OK.test(im.full)) return res.status(400).json({ success: false, code: "invalid_image" });
  for (const k of ["fabric", "label", "damage"]) if (im[k] && !OK.test(im[k])) return res.status(400).json({ success: false, code: "invalid_image" });
  // CONNECTION_TEST=1: structural reply to verify frontend<->API wiring only. NOT an AI prediction.
  if (!AI && process.env.CONNECTION_TEST === "1") return res.json({ success: true, connectionTest: true, fabricAI: { finalPrediction: "Unknown", confidence: 0, confidenceLevel: "LOW", agreement: "UNKNOWN" } });
  if (!AI) return res.status(503).json({ success: false, code: "ai_unavailable" });
  try {
    const r = await fetch(AI + "/analyze", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ images: im }), signal: AbortSignal.timeout(60000) });
    const j = await r.json().catch(() => null);
    if (!r.ok || !j) return res.status(503).json({ success: false, code: "ai_unavailable" });
    res.json({ success: true, ...j });
  } catch (e) { console.error("AI service error:", e.message); res.status(503).json({ success: false, code: "ai_unavailable" }); }
});
app.use((err, _q, res, _n) => res.status(err.status === 413 ? 413 : 400).json({ success: false, code: err.status === 413 ? "too_large" : "invalid_image" }));
app.listen(process.env.PORT || 8080, () => console.log("RE-THREAD API listening"));
