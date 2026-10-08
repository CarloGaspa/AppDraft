// Optional npm/pnpm shortcuts. Python remains the only release implementation.
import { existsSync } from "node:fs";
import { join } from "node:path";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";

const root = fileURLToPath(new URL("../", import.meta.url));
const python = join(root, ".venv", ...(process.platform === "win32"
  ? ["Scripts", "python.exe"] : ["bin", "python"]));

if (!existsSync(python)) {
  console.error("Ambiente .venv assente. Completa il setup descritto in docs/development.md.");
  process.exit(1);
}

const args = process.argv.slice(2).filter((arg) => arg !== "--");
const result = spawnSync(python, [join(root, "scripts", "release.py"), ...args,
  "--root", root, "--version-file", "pyproject.toml"], {
  cwd: root,
  stdio: "inherit",
  shell: false,
});

if (result.error) console.error(result.error.message);
if (result.signal) console.error(`Rilascio interrotto: ${result.signal}`);
process.exit(result.status ?? 1);
