import { accessSync, constants, readdirSync, realpathSync } from 'node:fs';
import * as path from 'node:path';

export interface PythonRuntime { executable: string; version: string }

// Never auto-discover executables supplied by the repository being inspected.
export function pythonCandidates(searchPath: string, roots: string[], extraDirectories: string[] = []): string[] {
  const normalize = (value: string) => { try { return realpathSync(value); } catch { return path.resolve(value); } };
  const excluded = roots.map(normalize);
  const safe = (value: string) => !excluded.some(root => {
    const relative = path.relative(root, normalize(value));
    return !relative || (!relative.startsWith('..' + path.sep) && relative !== '..' && !path.isAbsolute(relative));
  });
  const candidates: string[] = [];
  const seen = new Set<string>();
  for (const directory of [...new Set([...searchPath.split(path.delimiter), ...extraDirectories])]) {
    if (!path.isAbsolute(directory) || !safe(directory)) { continue; }
    let names: string[];
    try { names = readdirSync(directory).filter(name => /^python(?:3(?:\.\d+)?)?$/.test(name)); }
    catch { continue; }
    // Prefer the unversioned Python 3, then newest explicitly versioned installations.
    names.sort((a, b) => a === b ? 0 : a === 'python3' ? -1 : b === 'python3' ? 1 : b.localeCompare(a, undefined, { numeric: true }));
    for (const name of names) {
      const candidate = path.join(directory, name);
      const resolved = normalize(candidate);
      if (!safe(candidate) || seen.has(resolved)) { continue; }
      try { accessSync(candidate, constants.X_OK); } catch { continue; }
      seen.add(resolved); candidates.push(candidate);
    }
  }
  return candidates.slice(0, 12);
}

export async function discoverPython(
  candidates: string[], probe: (python: string) => Promise<PythonRuntime>, cancelled: () => boolean = () => false,
): Promise<PythonRuntime> {
  const failures: string[] = [];
  for (const candidate of [...new Set(candidates)].slice(0, 12)) {
    if (cancelled()) { throw new Error('Python discovery cancelled.'); }
    try {
      const result = await probe(candidate);
      const version = /^(\d+)\.(\d+)/.exec(result.version);
      if (!version || Number(version[1]) !== 3 || Number(version[2]) < 9 || !path.isAbsolute(result.executable)) {
        throw new Error('Python 3.9 or newer is required.');
      }
      return result;
    } catch (error) { failures.push(`${candidate}: ${error instanceof Error ? error.message : String(error)}`); }
  }
  if (cancelled()) { throw new Error('Python discovery cancelled.'); }
  throw new Error('No working Python 3.9+ found. Install Python 3 or run Thread: Configure Python (Advanced). ' + failures.join('\n').slice(0, 2000));
}
