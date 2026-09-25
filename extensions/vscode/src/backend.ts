import { spawn, ChildProcessWithoutNullStreams } from 'node:child_process';
import * as path from 'node:path';

export class Backend {
  private child?: ChildProcessWithoutNullStreams;
  private cancelled = false;
  get busy(): boolean { return this.child !== undefined; }
  cancel(): void { this.cancelled = true; this.child?.kill('SIGTERM'); }
  async call(python: string, extensionPath: string, request: object, timeoutMs = 650_000): Promise<any> {
    if (this.child) { throw new Error('A request is already running. Cancel it or wait.'); }
    this.cancelled = false;
    return new Promise((resolve, reject) => {
      const child = spawn(python, ['-I', '-u', path.join(extensionPath, 'python', 'bridge.py')],
        { cwd: extensionPath, shell: false, env: { ...process.env, PYTHONPATH: '', PYTHONSTARTUP: '' } });
      this.child = child;
      let output = '', errors = '', bytes = 0, settled = false;
      const timer = setTimeout(() => { this.cancelled = true; child.kill('SIGKILL'); }, timeoutMs);
      const finish = (error?: Error, value?: unknown) => {
        if (settled) { return; } settled = true; clearTimeout(timer); this.child = undefined;
        error ? reject(error) : resolve(value);
      };
      child.stdout.setEncoding('utf8');
      child.stdout.on('data', (data: string) => {
        bytes += Buffer.byteLength(data);
        if (bytes > 4 * 1024 * 1024) { child.kill('SIGKILL'); finish(new Error('Backend response exceeded 4 MiB.')); }
        else { output += data; }
      });
      child.stderr.on('data', (data: Buffer) => { if (errors.length < 4000) { errors += data.toString('utf8'); } });
      child.on('error', error => finish(new Error(`Cannot start Python: ${error.message}. Run Thread: Setup Local Model.`)));
      child.stdin.on('error', () => { /* close event reports a failed process */ });
      child.on('close', code => {
        if (this.cancelled) { finish(new Error('Request cancelled or timed out. No model actions were executed.')); return; }
        try {
          const envelope = JSON.parse(output);
          if (!envelope.ok || code !== 0) { finish(new Error(envelope.error || errors || 'Backend failed.')); }
          else { finish(undefined, envelope.result); }
        } catch { finish(new Error(errors || 'Python returned an invalid response. Check Python 3.9+ and the bundled backend.')); }
      });
      child.stdin.end(JSON.stringify(request) + '\n');
    });
  }
}
