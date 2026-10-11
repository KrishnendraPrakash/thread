// Scripted native host fixture: approvals below apply only to tiny synthetic assets.
import * as vscode from 'vscode';
import * as assert from 'node:assert/strict';
import * as path from 'node:path';
import { createHash } from 'node:crypto';
import { mkdir, writeFile, readFile, readdir } from 'node:fs/promises';
import { createServer } from 'node:http';
import { Agent } from '../extension';

export async function offlineCommandFixture(context: vscode.ExtensionContext, root: string): Promise<void> {
  const source = path.join(root, 'offline-command-source'), storage = path.join(root, 'offline-command-storage');
  await mkdir(source); await mkdir(storage);
  const manifest: any = { schema: 1, target: `${process.platform}-${process.arch}`, runtimeExecutable: 'runtime/ollama', runtimeVersion: '0.34.4', modelDirectory: 'models', model: 'fixture:tiny', assets: [] };
  for (const [name, role] of [['backend/thread-backend', 'backend'], ['runtime/ollama', 'runtime'], ['models/blob', 'model'], ['notices/LICENSE', 'notice']]) {
    const content = Buffer.from(role); await mkdir(path.dirname(path.join(source, name)), { recursive: true });
    await writeFile(path.join(source, name), content);
    manifest.assets.push({ path: name, role, size: content.length, sha256: createHash('sha256').update(content).digest('hex'), source: 'synthetic', license: 'test-only', version: 'fixture' });
  }
  await writeFile(path.join(source, 'bundle.json'), JSON.stringify(manifest));
  const previous = { directory: path.join(storage, 'previous'), executable: 'unused-fixture', models: 'unused-fixture', model: 'fixture:previous', version: '0.34.4', manifestSha256: 'fixture' };
  await mkdir(previous.directory); await writeFile(path.join(previous.directory, 'preserve'), 'prior installation');
  const globals = new Map<string, any>([['offlineInstallation', previous], ['managedRuntime', false]]);
  let failPersistence = false, goodMetadata = true;
  const isolatedContext = { ...context, globalStorageUri: vscode.Uri.file(storage), globalState: {
    get: (key: string, fallback: unknown) => globals.has(key) ? globals.get(key) : fallback,
    update: async (key: string, value: any) => { if (failPersistence && key === 'managedRuntime' && value === true) { failPersistence = false; throw new Error('Fixture persistence failure'); } globals.set(key, value); },
  }} as unknown as vscode.ExtensionContext;
  const server = createServer((request, response) => {
    assert.equal(request.url, '/api/show'); response.setHeader('Content-Type', 'application/json');
    response.end(JSON.stringify({ capabilities: goodMetadata ? ['completion'] : [] }));
  });
  await new Promise<void>((resolve, reject) => server.listen(0, '127.0.0.1', resolve).on('error', reject));
  const endpoint = `http://127.0.0.1:${(server.address() as any).port}`;
  const window = vscode.window as any, config = vscode.workspace.getConfiguration('thread');
  const previousModel = config.inspect<string>('model')?.globalValue;
  const original = { open: window.showOpenDialog, information: window.showInformationMessage, progress: window.withProgress };
  let consent = true, cancelCopy = false, reviews = 0, stops = 0;
  const notifications: string[] = [];
  try {
    window.showOpenDialog = async () => [vscode.Uri.file(source)];
    window.showInformationMessage = async (message: string, options: any) => {
      reviews++; assert.equal(options.modal, true); assert.match(message, /runs native code/); assert.match(message, /SHA-256/);
      return consent ? 'Import trusted bundle' : undefined;
    };
    window.withProgress = async (_options: any, task: any) => {
      let listener: (() => void) | undefined;
      return task({ report: () => { if (cancelCopy && listener) { cancelCopy = false; listener(); } } }, { onCancellationRequested: (callback: () => void) => { listener = callback; return { dispose: () => {} }; } });
    };
    function agent(): any {
      const instance: any = new Agent(isolatedContext); instance.notify = (message: string) => notifications.push(message);
      // Startup/metadata are controlled loopback responses; no synthetic native file is executed.
      instance.managed = { setOffline: () => {}, start: async () => endpoint, stop: () => { stops++; } };
      return instance;
    }
    await config.update('model', previous.model, vscode.ConfigurationTarget.Global);
    let instance = agent(); consent = false;
    try { await instance.importOfflineBundle(); assert.equal(globals.get('offlineInstallation'), previous); assert.deepEqual(await readdir(storage), ['previous']); }
    finally { instance.dispose(); }
    consent = true; goodMetadata = false; instance = agent();
    try {
      await assert.rejects(instance.importOfflineBundle(), /missing.*local completion/);
      assert.equal(globals.get('offlineInstallation'), previous); assert.equal(instance.managedMode, false);
      assert.equal(config.inspect<string>('model')?.globalValue, previous.model);
      assert.deepEqual(await readdir(path.join(storage, 'offline-bundles')), []);
      assert.equal(instance.setupController, undefined);
    } finally { instance.dispose(); }
    goodMetadata = true; failPersistence = true; instance = agent();
    try {
      await assert.rejects(instance.importOfflineBundle(), /persistence failure/);
      assert.equal(globals.get('offlineInstallation'), previous); assert.equal(globals.get('managedRuntime'), false);
      assert.equal(config.inspect<string>('model')?.globalValue, previous.model);
      assert.deepEqual(await readdir(path.join(storage, 'offline-bundles')), []);
    } finally { instance.dispose(); }
    cancelCopy = true; instance = agent();
    try { await instance.importOfflineBundle(); assert.equal(globals.get('offlineInstallation'), previous); assert.deepEqual(await readdir(path.join(storage, 'offline-bundles')), []); assert.ok(notifications.some(message => /cancelled/.test(message))); }
    finally { instance.dispose(); }
    instance = agent();
    try {
      await instance.importOfflineBundle(); const installed = globals.get('offlineInstallation');
      assert.notEqual(installed.directory, previous.directory); assert.equal(globals.get('managedRuntime'), true); assert.equal(instance.managedMode, true);
      assert.equal(config.inspect<string>('model')?.globalValue, manifest.model);
      assert.equal(await readFile(path.join(installed.directory, 'models/blob'), 'utf8'), 'model');
      assert.equal(await readFile(path.join(previous.directory, 'preserve'), 'utf8'), 'prior installation');
      assert.equal(instance.setupController, undefined); assert.equal(reviews, 5); assert.ok(stops >= 4);
    } finally { instance.dispose(); }
    console.log('THREAD_OFFLINE_COMMAND_FIXTURE_PASSED: modal consent/decline, production copy/state activation, metadata and persistence rollback, cancellation cleanup, prior installation/model preservation; synthetic startup, no manual UI certification');
  } finally {
    window.showOpenDialog = original.open; window.showInformationMessage = original.information; window.withProgress = original.progress;
    await config.update('model', previousModel, vscode.ConfigurationTarget.Global);
    await new Promise<void>(resolve => server.close(() => resolve()));
  }
}
