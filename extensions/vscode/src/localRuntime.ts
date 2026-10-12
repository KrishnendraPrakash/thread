import { spawn, ChildProcess } from 'node:child_process';
import { existsSync, readFileSync } from 'node:fs';
import { mkdir, statfs } from 'node:fs/promises';
import * as http from 'node:http';
import * as net from 'node:net';
import * as path from 'node:path';
import * as os from 'node:os';
import { bundledBackend, BACKEND_TARGETS } from './backend';
import { OfflineInstallation } from './offline';

export const RUNTIME_VERSION = '0.34.4';
export const MODEL_PROVISIONING = 'user-supplied';

export function localEndpoint(value: string): URL {
  const url = new URL(value);
  if (url.protocol !== 'http:' || url.hostname !== '127.0.0.1' || url.username || url.password || url.pathname !== '/' || url.search || url.hash) {
    throw new Error('Managed inference must use a direct IPv4 loopback endpoint.');
  }
  return url;
}

export function ollamaJson(endpoint: string, route: string, payload?: object, signal?: AbortSignal): Promise<any> {
  const base = localEndpoint(endpoint);
  if (route.split('?')[0] === '/api/pull') { return Promise.reject(new Error('Thread 0.2.1 requires user-supplied models; model downloads are disabled.')); }
  return new Promise((resolve, reject) => {
    const body = payload ? JSON.stringify(payload) : undefined;
    const request = http.request({ hostname: base.hostname, port: base.port || 11434, path: route, agent: false,
      method: body ? 'POST' : 'GET', signal, headers: { 'Content-Type': 'application/json' } }, response => {
      let output = '';
      response.setEncoding('utf8');
      response.on('data', chunk => { output += chunk; if (output.length > 1024 * 1024) { request.destroy(new Error('Ollama response too large.')); } });
      response.on('error', reject);
      response.on('end', () => {
        try {
          if (response.statusCode !== 200) { throw new Error(`Ollama returned HTTP ${response.statusCode}.`); }
          resolve(JSON.parse(output));
        } catch (error) { reject(error); }
      });
    });
    request.setTimeout(5000, () => request.destroy(new Error('Ollama check timed out.')));
    request.on('error', reject); request.end(body);
  });
}

export function runtimeSetupSupported(sourceOnly: boolean, platform: string, arch: string, darwinMajor: number, offline = false): boolean {
  const target = `${platform}-${arch}`;
  if (!(BACKEND_TARGETS as readonly string[]).includes(target) || (platform === 'darwin' && darwinMajor < 23)) { return false; }
  return !sourceOnly || offline || target === 'darwin-arm64';
}

export class LocalRuntime {
  private server?: ChildProcess;
  endpoint = 'http://127.0.0.1:11434';
  constructor(readonly directory: string, private offline?: OfflineInstallation, private sourceOnly = false) {}
  get storageDirectory(): string { return this.offline?.directory ?? this.directory; }
  setOffline(installation: OfflineInstallation): void { this.stop(); this.offline = installation; }
  get installed(): boolean {
    if (this.offline) { return existsSync(this.offline.executable); }
    try {
      const marker = JSON.parse(readFileSync(path.join(this.directory, `ollama-${RUNTIME_VERSION}`, 'installed.json'), 'utf8'));
      return marker.version === RUNTIME_VERSION && (marker.target === `${process.platform}-${process.arch}` || (!marker.target && process.platform === 'darwin'));
    } catch { return false; }
  }
  get supported(): boolean { return runtimeSetupSupported(this.sourceOnly, process.platform, process.arch, Number(os.release().split('.')[0]), !!this.offline); }
  get downloadBytes(): number {
    return process.platform === 'darwin' ? 160042307 : process.platform === 'linux'
      ? (process.arch === 'arm64' ? 1549684612 : 1427703051)
      : (process.arch === 'arm64' ? 208009666 : 1461155106);
  }
  async checkDisk(required: number): Promise<void> {
    await mkdir(this.storageDirectory, { recursive: true });
    const disk = await statfs(this.storageDirectory);
    if (disk.bavail * disk.bsize < required) { throw new Error(`Allow at least ${required / 1e9} GB free disk space for this setup.`); }
  }
  async install(python: string, extension: string, signal: AbortSignal, progress: (message: string) => void): Promise<void> {
    if (!this.supported) { throw new Error('No managed runtime profile for this OS/architecture. macOS requires version 14+.'); }
    await this.checkDisk(process.platform === 'linux' ? this.downloadBytes + 17e9
      : process.platform === 'win32' ? this.downloadBytes + 9e9 : 4e9);
    await new Promise<void>((resolve, reject) => {
      const args = python === bundledBackend(extension) ? ['install-runtime', this.directory]
        : ['-I', '-u', path.join(extension, 'python/install_runtime.py'), this.directory];
      const child = spawn(python, args,
        { shell: false, signal, cwd: extension, env: { ...process.env, PYTHONPATH: '', PYTHONSTARTUP: '' } });
      let errors = '';
      child.stderr.setEncoding('utf8');
      child.stderr.on('data', data => { errors = (errors + data).slice(-3000); progress(data.trim().slice(-200)); });
      child.stdout.resume();
      const timer = setTimeout(() => child.kill('SIGTERM'), 15 * 60 * 1000);
      child.on('error', reject);
      child.on('close', code => { clearTimeout(timer); code === 0 ? resolve() : reject(new Error(errors || 'Runtime installation cancelled or failed.')); });
    });
  }
  async start(signal?: AbortSignal): Promise<string> {
    if (this.server && this.server.exitCode === null && this.server.signalCode === null && !this.server.killed) { return this.endpoint; }
    if (!this.installed) { throw new Error('Managed runtime is not installed. Run setup.'); }
    const port = await new Promise<number>((resolve, reject) => {
      const reservation = net.createServer(); reservation.on('error', reject);
      reservation.listen(0, '127.0.0.1', () => { const port = (reservation.address() as net.AddressInfo).port; reservation.close(() => resolve(port)); });
    });
    signal?.throwIfAborted();
    this.endpoint = `http://127.0.0.1:${port}`;
    const executable = process.platform === 'win32' ? 'ollama.exe' : process.platform === 'linux' ? 'bin/ollama' : 'ollama';
    const child = spawn(this.offline?.executable ?? path.join(this.directory, `ollama-${RUNTIME_VERSION}`, executable), ['serve'], {
      cwd: this.offline?.directory ?? this.directory, shell: false, env: { ...process.env, OLLAMA_HOST: this.endpoint, OLLAMA_MODELS: this.offline?.models ?? path.join(this.directory, 'models'),
        OLLAMA_NO_CLOUD: '1', OLLAMA_CONTEXT_LENGTH: '16384', OLLAMA_NUM_PARALLEL: '1' },
      stdio: ['ignore', 'ignore', 'pipe'],
    });
    this.server = child;
    let failure = '', stderr = '';
    child.on('error', error => { failure = error.message; });
    child.stderr?.on('data', data => { stderr = (stderr + data.toString()).slice(-2000); });
    try {
      for (let i = 0; i < 60; i++) {
        signal?.throwIfAborted();
        if (failure || child.exitCode !== null || child.signalCode !== null) { throw new Error(failure || stderr || 'Managed runtime stopped.'); }
        try {
          const result = await ollamaJson(this.endpoint, '/api/version', undefined, signal);
          if (result.version === (this.offline?.version ?? RUNTIME_VERSION) && child.exitCode === null) { return this.endpoint; }
        } catch { signal?.throwIfAborted(); }
        await new Promise(resolve => setTimeout(resolve, 250));
      }
      throw new Error('Managed runtime did not become ready.');
    } catch (error) { this.stop(); throw error; }
  }
  stop(): void { this.server?.kill('SIGTERM'); this.server = undefined; this.endpoint = 'http://127.0.0.1:11434'; }
}
