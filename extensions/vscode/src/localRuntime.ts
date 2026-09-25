import { spawn, ChildProcess } from 'node:child_process';
import { existsSync } from 'node:fs';
import { mkdir, statfs } from 'node:fs/promises';
import * as http from 'node:http';
import * as net from 'node:net';
import * as path from 'node:path';
import * as os from 'node:os';

export const RUNTIME_VERSION = '0.34.4';
export const STARTER_MODELS = [
  { name: 'qwen2.5-coder:1.5b', size: 'about 986 MB', disk: 4e9, description: 'Small download; limited reasoning quality. Apache 2.0.' },
  { name: 'qwen2.5-coder:7b', size: 'about 4.7 GB', disk: 10e9, description: 'Larger coding model; allow more memory. Apache 2.0.' },
];

export function localEndpoint(value: string): URL {
  const url = new URL(value);
  if (url.protocol !== 'http:' || url.hostname !== '127.0.0.1' || url.username || url.password || url.pathname !== '/' || url.search || url.hash) {
    throw new Error('Managed inference must use a direct IPv4 loopback endpoint.');
  }
  return url;
}

export function ollamaJson(endpoint: string, route: string, payload?: object, signal?: AbortSignal): Promise<any> {
  const base = localEndpoint(endpoint);
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

export function pullModel(endpoint: string, model: string, signal: AbortSignal, progress: (text: string) => void): Promise<void> {
  const base = localEndpoint(endpoint);
  if (!STARTER_MODELS.some(item => item.name === model)) { return Promise.reject(new Error('Choose a listed starter model.')); }
  return new Promise((resolve, reject) => {
    let pending = '', success = false;
    const request = http.request({ hostname: base.hostname, port: base.port || 11434, path: '/api/pull', method: 'POST', signal, agent: false,
      headers: { 'Content-Type': 'application/json' } }, response => {
      response.setEncoding('utf8');
      const consume = (line: string) => {
        if (!line.trim()) { return; }
        const data = JSON.parse(line);
        if (data.error) { throw new Error(String(data.error)); }
        success = data.status === 'success';
        const percent = typeof data.total === 'number' && data.total > 0 && typeof data.completed === 'number'
          ? ` ${Math.min(100, Math.round(100 * data.completed / data.total))}%` : '';
        progress(`${String(data.status ?? 'Downloading model').slice(0, 120)}${percent}`);
      };
      response.on('data', chunk => {
        try {
          pending += chunk;
          if (pending.length > 1024 * 1024) { throw new Error('Invalid model download progress.'); }
          let newline: number;
          while ((newline = pending.indexOf('\n')) >= 0) { consume(pending.slice(0, newline)); pending = pending.slice(newline + 1); }
        } catch (error) { reject(error); response.destroy(); request.destroy(); }
      });
      response.on('error', reject);
      response.on('end', () => {
        try {
          consume(pending);
          if (response.statusCode !== 200 || !success) { throw new Error('Model download did not complete. Retry setup.'); }
          resolve();
        } catch (error) { reject(error); }
      });
    });
    const timer = setTimeout(() => request.destroy(new Error('Model download exceeded one hour. Retry setup to reuse partial downloads.')), 3600000);
    request.setTimeout(60000, () => request.destroy(new Error('Model download stalled. Retry setup.')));
    request.on('error', reject); request.on('close', () => clearTimeout(timer));
    request.end(JSON.stringify({ model, stream: true }));
  });
}

export class LocalRuntime {
  private server?: ChildProcess;
  endpoint = 'http://127.0.0.1:11434';
  constructor(readonly directory: string) {}
  get installed(): boolean { return existsSync(path.join(this.directory, `ollama-${RUNTIME_VERSION}`, 'installed.json')); }
  get supported(): boolean { return process.platform === 'darwin' && process.arch === 'arm64' && Number(os.release().split('.')[0]) >= 23; }
  async checkDisk(required: number): Promise<void> {
    await mkdir(this.directory, { recursive: true });
    const disk = await statfs(this.directory);
    if (disk.bavail * disk.bsize < required) { throw new Error(`Allow at least ${required / 1e9} GB free disk space for this setup.`); }
  }
  async install(python: string, extension: string, signal: AbortSignal, progress: (message: string) => void): Promise<void> {
    if (!this.supported) { throw new Error('Managed runtime installation currently supports Apple Silicon on macOS 14+. Use existing Ollama on other supported systems.'); }
    await this.checkDisk(4e9);
    await new Promise<void>((resolve, reject) => {
      const child = spawn(python, ['-I', '-u', path.join(extension, 'python/install_runtime.py'), this.directory],
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
    const child = spawn(path.join(this.directory, `ollama-${RUNTIME_VERSION}`, 'ollama'), ['serve'], {
      cwd: this.directory, shell: false, env: { ...process.env, OLLAMA_HOST: this.endpoint, OLLAMA_MODELS: path.join(this.directory, 'models'),
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
          if (result.version === RUNTIME_VERSION && child.exitCode === null) { return this.endpoint; }
        } catch { signal?.throwIfAborted(); }
        await new Promise(resolve => setTimeout(resolve, 250));
      }
      throw new Error('Managed runtime did not become ready.');
    } catch (error) { this.stop(); throw error; }
  }
  stop(): void { this.server?.kill('SIGTERM'); this.server = undefined; this.endpoint = 'http://127.0.0.1:11434'; }
}
