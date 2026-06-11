import fs from "fs";
import path from "path";

export function findGeneratedFile(filename: string): string | null {
  const cwd = process.cwd();
  const candidates = [
    path.join(cwd, "public", "data", filename),
    path.join(cwd, "frontend", "public", "data", filename),
    path.join(cwd, "..", "frontend", "public", "data", filename),
    path.join(cwd, "output", filename),
    path.join(cwd, "..", "output", filename),
  ];

  return candidates.find((candidate) => fs.existsSync(candidate)) ?? null;
}

export function findLogFile(filename: string): string | null {
  const cwd = process.cwd();
  const candidates = [
    path.join(cwd, "..", "logs", filename),
    path.join(cwd, "logs", filename),
    path.join(cwd, "public", "data", filename),
    path.join(cwd, "frontend", "public", "data", filename),
    path.join(cwd, "..", "frontend", "public", "data", filename),
  ];

  return candidates.find((candidate) => fs.existsSync(candidate)) ?? null;
}
