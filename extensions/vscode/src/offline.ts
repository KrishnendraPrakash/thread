import { constants } from 'node:fs';
import { lstat, readFile, writeFile, mkdir, open, rename, rm, rmdir, statfs, chmod } from 'node:fs/promises';
import { createHash, randomBytes } from 'node:crypto';
import * as path from 'node:path';
import { BACKEND_TARGETS } from './backend';

export interface OfflineAsset { path: string; role: string; size: number; sha256: string; source: string; license: string; version: string; executable?: boolean }
export interface OfflineManifest {
  schema: number; target: string; assets: OfflineAsset[];
  runtimeExecutable: string; modelDirectory: string; model: string; runtimeVersion: string;
}
export interface OfflineInstallation { directory: string; executable: string; models: string; model: string; version: string; manifestSha256: string }

function parseManifest(raw: Buffer): OfflineManifest {
  const text = raw.toString('utf8');
  const parsed = JSON.parse(text); // First validate JSON syntax; tokenizer below only checks duplicate keys.
  const stack: Array<{ object: boolean; key: boolean; names: Set<string> }> = [];
  for (const match of text.matchAll(/"(?:\\.|[^"\\])*"|[{}\[\],]/g)) {
    const token = match[0], current = stack[stack.length - 1];
    if (token === '{' || token === '[') { stack.push({ object: token === '{', key: token === '{', names: new Set() }); }
    else if (token === '}' || token === ']') { stack.pop(); }
    else if (token === ',') { if (current?.object) { current.key = true; } }
    else if (current?.object && current.key) {
      const name = JSON.parse(token) as string;
      if (current.names.has(name)) { throw new Error('Offline manifest contains duplicate object keys.'); }
      current.names.add(name); current.key = false;
    }
  }
  return parsed as OfflineManifest;
}

function relative(value: unknown): string {
  if (typeof value !== 'string' || !value || value.length > 500 || /[\\:\x00-\x1f<>"|?*]/.test(value) || value.split('/').some(part => !part || part === '.' || part === '..' || /[. ]$/.test(part) || /^(con|prn|aux|nul|clock\$|com[1-9¹²³]|lpt[1-9¹²³])(?:\.|$)/i.test(part))) {
    throw new Error('Unsafe offline asset path.');
  }
  return value;
}
async function regular(root: string, name: string): Promise<string> {
  let item = root;
  if (!(await lstat(root)).isDirectory() || (await lstat(root)).isSymbolicLink()) { throw new Error('Select a regular offline bundle directory.'); }
  for (const part of relative(name).split('/')) {
    item = path.join(item, part);
    if ((await lstat(item)).isSymbolicLink()) { throw new Error('Offline assets cannot contain links.'); }
  }
  const info = await lstat(item);
  if (!info.isFile() || info.nlink !== 1) { throw new Error('Offline assets must be unlinked regular files.'); }
  return item;
}
export async function inspectOffline(root: string, target: string): Promise<{ manifest: OfflineManifest; digest: string; bytes: number; raw: Buffer }> {
  if (!(BACKEND_TARGETS as readonly string[]).includes(target) || !path.isAbsolute(root)) { throw new Error('Unsupported offline target or directory.'); }
  const filename = await regular(root, 'bundle.json');
  if ((await lstat(filename)).size > 1024 * 1024) { throw new Error('Offline manifest exceeds 1 MiB.'); }
  const raw = await readFile(filename);
  if (raw.length > 1024 * 1024) { throw new Error('Offline manifest grew beyond 1 MiB.'); }
  const manifest = parseManifest(raw);
  if (!manifest || typeof manifest !== 'object' || manifest.schema !== 1 || manifest.target !== target || !Array.isArray(manifest.assets) || !manifest.assets.length || manifest.assets.length > 10000) { throw new Error('Offline bundle schema, target or inventory is invalid.'); }
  const names = new Set<string>(), roles = new Set<string>();
  let bytes = 0;
  for (const asset of manifest.assets) {
    if (!asset || typeof asset !== 'object') { throw new Error('Invalid offline asset record.'); }
    const name = relative(asset.path);
    if (names.has(name.toLowerCase()) || ['bundle.json', 'import.json'].includes(name.toLowerCase()) || !Number.isSafeInteger(asset.size) || asset.size < 0 || !/^[a-f0-9]{64}$/.test(asset.sha256) || !['role', 'source', 'license', 'version'].every(key => typeof (asset as any)[key] === 'string' && (asset as any)[key].trim())) { throw new Error('Invalid offline asset identity, size, checksum or provenance.'); }
    names.add(name.toLowerCase()); roles.add(asset.role); bytes += asset.size;
    if (asset.executable !== undefined && (typeof asset.executable !== 'boolean' || (asset.executable && !['backend', 'runtime'].includes(asset.role)))) { throw new Error('Executable flags are allowed only for native backend/runtime assets.'); }
    if (!Number.isSafeInteger(bytes) || bytes > 100 * 1024 ** 3) { throw new Error('Offline bundle exceeds 100 GiB.'); }
  }
  for (const name of names) {
    const parts = name.split('/');
    if (['bundle.json', 'import.json'].includes(parts[0]) || parts.slice(0, -1).some((_, index) => names.has(parts.slice(0, index + 1).join('/')))) { throw new Error('Offline asset paths conflict with files or import metadata.'); }
  }
  if (!['backend', 'runtime', 'model', 'notice'].every(role => roles.has(role))) { throw new Error('Offline companion needs backend, runtime, model and notice assets.'); }
  relative(manifest.runtimeExecutable); relative(manifest.modelDirectory);
  if (!manifest.assets.some(asset => asset.path === manifest.runtimeExecutable && asset.role === 'runtime') || !manifest.assets.some(asset => asset.path.startsWith(manifest.modelDirectory + '/') && asset.role === 'model') || typeof manifest.model !== 'string' || !/^[A-Za-z0-9][A-Za-z0-9._:/-]{0,199}$/.test(manifest.model) || /cloud/i.test(manifest.model) || !/^\d+\.\d+\.\d+$/.test(manifest.runtimeVersion)) { throw new Error('Invalid runtime or local model configuration.'); }
  return { manifest, digest: createHash('sha256').update(raw).digest('hex'), bytes, raw };
}

// Call only after the user confirms the inspected manifest digest and native-code import.
// Source files are streamed into private staging and their copied bytes are verified.
export async function importOffline(root: string, storage: string, target: string, approvedDigest: string, signal: AbortSignal, progress: (message: string) => void): Promise<OfflineInstallation> {
  const inspected = await inspectOffline(root, target);
  if (inspected.digest !== approvedDigest) { throw new Error('Offline manifest changed after review.'); }
  signal.throwIfAborted();
  await mkdir(storage, { recursive: true });
  if ((await lstat(storage)).isSymbolicLink()) { throw new Error('Offline storage cannot be a link.'); }
  const disk = await statfs(storage);
  if (disk.bavail * disk.bsize < inspected.bytes + 1024 * 1024) { throw new Error('Insufficient disk space for offline import.'); }
  const lock = path.join(storage, 'import.lock');
  try { await mkdir(lock); }
  catch (error) {
    if ((error as NodeJS.ErrnoException).code === 'EEXIST') { throw new Error('Another offline import is active. If a prior process crashed, close all Thread windows before removing only import.lock.'); }
    throw error;
  }
  const staging = path.join(storage, 'staging-' + randomBytes(12).toString('hex'));
  const final = path.join(storage, 'bundle-' + randomBytes(12).toString('hex'));
  try {
    await mkdir(staging);
    for (const asset of inspected.manifest.assets) {
      signal.throwIfAborted(); progress(`Verifying ${asset.path}`); signal.throwIfAborted();
      const source = await regular(root, asset.path);
      const destination = path.join(staging, ...asset.path.split('/'));
      await mkdir(path.dirname(destination), { recursive: true });
      const input = await open(source, constants.O_RDONLY | (constants.O_NOFOLLOW ?? 0));
      try {
        const before = await input.stat();
        if (!before.isFile() || before.nlink !== 1 || before.size !== asset.size) { throw new Error('Offline asset size or type changed.'); }
        const output = await open(destination, 'wx', 0o600);
        const digest = createHash('sha256'); let copied = 0;
        try {
          signal.throwIfAborted();
          const reader = input.createReadStream({ autoClose: false, highWaterMark: 1024 * 1024, signal });
          // The iterator reports errors; retain a listener for deferred abort events during teardown.
          reader.on('error', () => {});
          for await (const chunk of reader) {
            signal.throwIfAborted(); copied += chunk.length;
            if (copied > asset.size) { throw new Error('Offline asset grew during import.'); }
            digest.update(chunk);
            let offset = 0;
            while (offset < chunk.length) {
              const written = (await output.write(chunk, offset, chunk.length - offset)).bytesWritten;
              if (!written) { throw new Error('Offline copy made no progress.'); }
              offset += written;
            }
            progress(`Copied ${asset.path}: ${copied}/${asset.size} bytes`);
            signal.throwIfAborted();
          }
          if (copied !== asset.size || digest.digest('hex') !== asset.sha256) { throw new Error('Offline asset checksum mismatch.'); }
        } finally { await output.close(); }
      } finally { await input.close(); }
      if (asset.executable === true || (asset.executable === undefined && asset.role === 'backend') || asset.path === inspected.manifest.runtimeExecutable) { await chmod(destination, 0o755); }
    }
    signal.throwIfAborted();
    if ((await inspectOffline(root, target)).digest !== approvedDigest) { throw new Error('Offline manifest changed during import.'); }
    await writeFile(path.join(staging, 'bundle.json'), inspected.raw, { flag: 'wx', mode: 0o600 });
    await writeFile(path.join(staging, 'import.json'), JSON.stringify({ manifestSha256: approvedDigest, target, importedAt: new Date().toISOString(), producer: 'Thread offline importer', modelInferenceChecked: false }), { flag: 'wx', mode: 0o600 });
    signal.throwIfAborted();
    await rename(staging, final);
    return { directory: final, executable: path.join(final, ...inspected.manifest.runtimeExecutable.split('/')), models: path.join(final, ...inspected.manifest.modelDirectory.split('/')), model: inspected.manifest.model, version: inspected.manifest.runtimeVersion, manifestSha256: approvedDigest };
  } catch (error) { await rm(staging, { recursive: true, force: true }); throw error; }
  finally { await rmdir(lock); }
}
