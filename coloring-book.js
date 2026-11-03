import { randomUUID } from "node:crypto";
import { join } from "node:path";

const DEFAULT_COMFY_URL = "http://127.0.0.1:8188";
const CHECKPOINT = process.env.COLORING_BOOK_CHECKPOINT || "v1-5-pruned-emaonly-fp16.safetensors";
const CHRISTMAS_STYLE = [
  "printable adult coloring book illustration",
  "cozy Christmas aesthetic, charming simple composition",
  "pure black ink line art on a completely white background",
  "very bold, thick, smooth, uniform solid black outlines",
  "crisp closed contours, clean vector-like coloring page",
  "large open enclosed areas and maximum coloring space",
  "minimal interior detail, uncluttered composition",
  "single centered scene, balanced composition, generous white margins",
  "black and white only, no lettering, no watermark"
].join(", ");

const NEGATIVE = [
  "gray, grey, grayscale shading, shadows, gradients, fading, faint lines",
  "thin lines, sketch lines, pencil, rough strokes, broken outlines",
  "hatching, crosshatching, stippling, texture, tiny intricate patterns",
  "color, colored ink, filled black areas, solid black background",
  "photorealistic, 3d, rendering, clutter, busy background",
  "text, letters, words, logo, watermark, border, frame",
  "cropped subject, cut off objects, incomplete drawing"
].join(", ");

function getComfyUrl() {
  const raw = process.env.COMFYUI_URL || DEFAULT_COMFY_URL;
  const url = new URL(raw);
  const allowedHosts = new Set(["127.0.0.1", "localhost", "::1"]);
  if (url.protocol !== "http:" || !allowedHosts.has(url.hostname)) {
    throw new Error("COMFYUI_URL must point to a local HTTP ComfyUI server.");
  }
  return url.origin;
}

function localOnly(req, res, next) {
  const address = req.socket.remoteAddress || "";
  const allowed = new Set(["127.0.0.1", "::1", "::ffff:127.0.0.1"]);
  if (!allowed.has(address)) {
    return res.status(403).json({ error: "Coloring-book controls are available only from this computer." });
  }
  next();
}

async function comfyFetch(path, options = {}) {
  const response = await fetch(new URL(path, getComfyUrl()), {
    ...options,
    signal: AbortSignal.timeout(15000),
    headers: { ...(options.headers || {}) }
  });
  const body = await response.text();
  let data;
  try { data = body ? JSON.parse(body) : {}; }
  catch { data = { message: body.slice(0, 1000) }; }
  if (!response.ok) {
    const error = new Error(data.error || data.message || `ComfyUI returned HTTP ${response.status}`);
    error.status = response.status;
    throw error;
  }
  return data;
}

function makeWorkflow(scene, pageNumber, seed) {
  const safePage = String(pageNumber).padStart(3, "0");
  const positive = `${CHRISTMAS_STYLE}. Scene: ${scene}. Draw a clear, simple, charming Christmas illustration with a few large recognizable objects. Keep every shape spacious and easy to color.`;
  return {
    "1": { class_type: "CheckpointLoaderSimple", inputs: { ckpt_name: CHECKPOINT } },
    "2": { class_type: "CLIPTextEncode", inputs: { text: positive, clip: ["1", 1] } },
    "3": { class_type: "CLIPTextEncode", inputs: { text: NEGATIVE, clip: ["1", 1] } },
    "4": { class_type: "EmptyLatentImage", inputs: { width: 512, height: 512, batch_size: 1 } },
    "5": { class_type: "KSampler", inputs: {
      seed, steps: 22, cfg: 7, sampler_name: "euler", scheduler: "normal",
      denoise: 1, model: ["1", 0], positive: ["2", 0], negative: ["3", 0], latent_image: ["4", 0]
    } },
    "6": { class_type: "VAEDecode", inputs: { samples: ["5", 0], vae: ["1", 2] } },
    "7": { class_type: "SaveImage", inputs: {
      filename_prefix: `Pages/Page_${safePage}`, images: ["6", 0]
    } }
  };
}

async function submitScene(scene, pageNumber) {
  const seed = Math.floor(Math.random() * 2 ** 32);
  const workflow = makeWorkflow(scene, pageNumber, seed);
  const result = await comfyFetch("/prompt", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ prompt: workflow, client_id: randomUUID() })
  });
  return { pageNumber, scene, seed, promptId: result.prompt_id, nodeErrors: result.node_errors || {} };
}

export function registerColoringBookRoutes(app) {
  app.use("/coloring-book", localOnly);

  app.get("/coloring-book/status", async (_req, res) => {
    try {
      const [stats, queue] = await Promise.all([comfyFetch("/system_stats"), comfyFetch("/queue")]);
      res.json({
        ok: true, connected: true, comfyUrl: getComfyUrl(),
        device: stats.devices?.[0] || stats.system?.devices?.[0] || null,
        queue: { running: queue.queue_running?.length || 0, pending: queue.queue_pending?.length || 0 },
        checkpoint: CHECKPOINT
      });
    } catch (error) {
      res.status(503).json({ ok: false, connected: false, error: error.message, hint: "Start ComfyUI locally, then try again." });
    }
  });

  // High-level single-page creation: the agent supplies a scene, not a ComfyUI graph.
  app.post("/coloring-book/create", async (req, res) => {
    try {
      const scene = String(req.body?.scene || "").trim().slice(0, 600);
      if (!scene) return res.status(400).json({ error: "Provide a short Christmas scene description in 'scene'." });
      const pageNumber = Math.max(1, Math.min(999, Number.parseInt(req.body?.pageNumber, 10) || 1));
      const result = await submitScene(scene, pageNumber);
      const outputDirectory = process.env.COLORING_BOOK_ROOT || "D:/Coloring Books/Cozy Christmas Coloring Book";
      res.status(202).json({ ok: true, ...result, outputDirectory: join(outputDirectory, "Pages") });
    } catch (error) {
      res.status(error.status || 502).json({ ok: false, error: error.message });
    }
  });

  // Queue a small batch at once. ComfyUI processes jobs sequentially; keep batches modest on low-VRAM GPUs.
  app.post("/coloring-book/batch", async (req, res) => {
    try {
      const scenes = req.body?.scenes;
      if (!Array.isArray(scenes) || scenes.length < 1 || scenes.length > 5) {
        return res.status(400).json({ error: "Provide between 1 and 5 scene descriptions in 'scenes'." });
      }
      const startPage = Math.max(1, Math.min(999, Number.parseInt(req.body?.startPage, 10) || 1));
      const jobs = [];
      for (let i = 0; i < scenes.length; i++) {
        const scene = String(scenes[i] || "").trim().slice(0, 600);
        if (!scene) return res.status(400).json({ error: `Scene ${i + 1} is empty.` });
        jobs.push(await submitScene(scene, startPage + i));
      }
      res.status(202).json({ ok: true, count: jobs.length, jobs });
    } catch (error) {
      res.status(error.status || 502).json({ ok: false, error: error.message });
    }
  });

  app.post("/coloring-book/queue", async (req, res) => {
    try {
      const workflow = req.body?.workflow;
      if (!workflow || typeof workflow !== "object" || Array.isArray(workflow)) {
        return res.status(400).json({ error: "Provide a ComfyUI API-format workflow object in 'workflow'." });
      }
      const result = await comfyFetch("/prompt", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt: workflow, client_id: String(req.body?.client_id || randomUUID()).slice(0, 128) })
      });
      res.status(202).json({ ok: true, promptId: result.prompt_id, nodeErrors: result.node_errors || {} });
    } catch (error) {
      res.status(error.status || 502).json({ ok: false, error: error.message });
    }
  });

  app.get("/coloring-book/history/:promptId", async (req, res) => {
    try {
      const promptId = String(req.params.promptId || "");
      if (!/^[a-zA-Z0-9-]{1,128}$/.test(promptId)) return res.status(400).json({ error: "Invalid prompt ID." });
      const result = await comfyFetch(`/history/${encodeURIComponent(promptId)}`);
      res.json({ ok: true, history: result[promptId] || null });
    } catch (error) {
      res.status(error.status || 502).json({ ok: false, error: error.message });
    }
  });
}
