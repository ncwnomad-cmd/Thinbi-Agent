import { execFile } from "node:child_process";
import { promisify } from "node:util";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const execFileAsync = promisify(execFile);
const HERE = dirname(fileURLToPath(import.meta.url));
const SCRIPT = join(HERE, "assemble-coloring-book.py");
const PYTHON = process.env.COLORING_BOOK_PYTHON || process.env.PYTHON || "python";
const DEFAULT_ROOT = "D:\\Coloring Books\\Cozy Christmas Coloring Book";

function localOnly(req, res, next) {
  const address = req.socket.remoteAddress || "";
  if (!new Set(["127.0.0.1", "::1", "::ffff:127.0.0.1"]).has(address)) {
    return res.status(403).json({ error: "Coloring-book controls are available only from this computer." });
  }
  next();
}

export function registerColoringBookAssemblyRoute(app) {
  app.post("/coloring-book/assemble", localOnly, async (req, res) => {
    const requested = req.body?.targetIllustrations ?? req.body?.targetPages;
    const targetIllustrations = Number.parseInt(requested, 10) || 50;
    if (targetIllustrations < 1 || targetIllustrations > 50) {
      return res.status(400).json({ ok: false, error: "targetIllustrations must be between 1 and 50. A 100-page interior uses 50 illustrations plus 50 blank backs." });
    }

    const root = process.env.COLORING_BOOK_ROOT || DEFAULT_ROOT;
    const args = [SCRIPT, "--target-illustrations", String(targetIllustrations)];
    if (req.body?.allowIncomplete === true) args.push("--allow-incomplete");

    try {
      const { stdout } = await execFileAsync(PYTHON, args, {
        windowsHide: true,
        timeout: 600000,
        maxBuffer: 2 * 1024 * 1024,
        env: { ...process.env, COLORING_BOOK_ROOT: root }
      });
      let report;
      try { report = JSON.parse(stdout); }
      catch { report = { output: stdout }; }
      res.json({ ok: true, report });
    } catch (error) {
      let report = null;
      try { report = JSON.parse(error.stdout || ""); } catch {}
      res.status(error.code === 2 ? 409 : 500).json({
        ok: false,
        error: error.message,
        report,
        stderr: String(error.stderr || "").slice(-3000)
      });
    }
  });
}
