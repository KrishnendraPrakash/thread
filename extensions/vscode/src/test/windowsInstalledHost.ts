import * as vscode from 'vscode';
import * as assert from 'node:assert/strict';
import * as path from 'node:path';
import { existsSync, lstatSync, readFileSync, realpathSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { spawnSync } from 'node:child_process';

export async function run(): Promise<void> {
  assert.equal(process.platform, 'win32'); assert.equal(process.arch, 'x64');
  const extension = vscode.extensions.getExtension('Krishnendra.thread-agent');
  assert.ok(extension, 'Actual installed extension must be registered');
  assert.equal(realpathSync(extension.extensionPath), realpathSync(process.env.THREAD_INSTALLED_PATH!));
  assert.equal(extension.packageJSON.version, process.env.THREAD_INSTALLED_VERSION);
  assert.equal(extension.packageJSON.license, 'MIT');
  const license = readFileSync(path.join(extension.extensionPath, 'LICENSE.txt'));
  assert.equal(createHash('sha256').update(license).digest('hex'), process.env.THREAD_INSTALLED_LICENSE_SHA);
  assert.equal(existsSync(path.join(extension.extensionPath, 'python/bridge.py')), false);
  const native = path.join(extension.extensionPath, 'native/win32-x64/thread-backend/thread-backend.exe');
  assert.ok(lstatSync(native).isFile()); assert.equal(lstatSync(native).isSymbolicLink(), false);
  const probe = spawnSync(native, [], { input: JSON.stringify({ operation: 'python' })+'\n', encoding: 'utf8', timeout: 30000,
    env: { ...process.env, PATH: 'C:\\nonexistent\\thread-no-python', PYTHONPATH: 'C:\\nonexistent', PYTHONHOME: 'C:\\nonexistent' } });
  assert.equal(probe.status, 0, probe.stderr);
  const envelope = JSON.parse(probe.stdout); assert.equal(envelope.ok, true); assert.equal(envelope.result.bundled, true);
  assert.equal(realpathSync(envelope.result.executable), realpathSync(native));
  await extension.activate(); assert.equal(extension.isActive, true);
  const commands = await vscode.commands.getCommands(true);
  for (const suffix of ['importOffline','setup','configurePython','ask','debug','feature','summary','review','cancel','clear','runTask']) {
    assert.ok(commands.includes('thread.'+suffix), 'Missing installed command '+suffix);
  }
  await vscode.commands.executeCommand('thread.sidebar.focus');
  const errors: string[] = [], window: any = vscode.window;
  const original = window.showErrorMessage;
  window.showErrorMessage = async (message: string) => { errors.push(message); return undefined; };
  try {
    await vscode.commands.executeCommand('thread.setup');
    assert.ok(errors.some(message => /supports macOS and Linux/.test(message)), 'Actual command must retain the Windows guard');
  } finally { window.showErrorMessage = original; }
  console.log('THREAD_WINDOWS_INSTALLED_HOST_PASSED: exact installed version/license, native no-Python probe, activation/commands/sidebar, expected guarded setup rejection');
  console.log('LIMITS: development-mode test host over installed payload; runner has developer tools/admin rights; no bare-machine or positive setup/edit/inference certification');
}
