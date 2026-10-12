// Private transformed candidate only. Real installed commands/native edits;
// synthetic HTTP responses and scripted approvals are not human/model evidence.
import * as vscode from 'vscode';
import * as assert from 'node:assert/strict';
import * as path from 'node:path';
import { readFileSync, realpathSync, writeFileSync } from 'node:fs';
import { createServer } from 'node:http';

export async function run(): Promise<void> {
  assert.equal(process.platform, 'win32'); assert.equal(vscode.workspace.isTrusted, true);
  const extension = vscode.extensions.getExtension('Krishnendra.thread-agent')!;
  await extension.activate();
  assert.equal(realpathSync(extension.extensionPath), realpathSync(process.env.THREAD_INSTALLED_PATH!));
  const main = path.resolve(extension.extensionPath, extension.packageJSON.main);
  const loaded = Object.values(require.cache).find(module => module && path.resolve(module.filename).toLowerCase() === main.toLowerCase())!;
  assert.ok(loaded);
  const bytes = readFileSync(main, 'utf8');
  assert.ok(bytes.includes('Trust this workspace before using Thread.'));
  assert.equal(bytes.includes('This experimental backend currently supports macOS and Linux.'), false);
  const installedAPI = loaded.require('vscode');
  const Agent = loaded.exports.Agent;
  const root = vscode.workspace.workspaceFolders![0].uri.fsPath;
  const app = path.join(root, 'app.py');
  const original = { pick: installedAPI.window.showQuickPick, input: installedAPI.window.showInputBox,
    info: installedAPI.window.showInformationMessage, warning: installedAPI.window.showWarningMessage,
    error: installedAPI.window.showErrorMessage, setup: Agent.prototype.setup, review: Agent.prototype.review };
  let agent: any;
  const errors: string[] = [], picks: string[] = [], prompts: string[] = [];
  let approvals = 0, diffConfirmations = 0;
  installedAPI.window.showQuickPick = async (items: any[]) => {
    const key = picks.shift(); assert.ok(key, 'Unexpected picker');
    if (key === 'file') return items[0];
    const selected = items.find(item => (typeof item === 'string' ? item : item.key || item.label) === key);
    assert.ok(selected, 'Missing choice '+key); return selected;
  };
  installedAPI.window.showInputBox = async () => { const prompt = prompts.shift(); assert.ok(prompt); return prompt; };
  installedAPI.window.showInformationMessage = async (message: string) => {
    if (message.startsWith('Inspect ')) { diffConfirmations++; return 'Reviewed this diff'; }
    return undefined;
  };
  installedAPI.window.showWarningMessage = async (message: string, options: any) => {
    assert.equal(options.modal, true);
    if (message.startsWith('Apply this exact proposal')) { approvals++; return 'Apply reviewed changes'; }
    return undefined;
  };
  installedAPI.window.showErrorMessage = async (message: string) => { errors.push(message); return undefined; };
  Agent.prototype.setup = async function () { agent = this; return original.setup.call(this); };
  Agent.prototype.review = async function () { agent = this; return original.review.call(this); };
  let changes: any[] = [];
  let requests = 0;
  const server = createServer((request, response) => {
    let body = ''; request.on('data', chunk => { body += chunk; });
    request.on('end', () => {
      let value: any;
      if (request.url === '/api/tags') value = { models: [{ name: 'fixture:local', digest: 'synthetic' }] };
      else if (request.url === '/api/version') value = { version: 'synthetic' };
      else if (request.url === '/api/show') value = { capabilities: ['completion'], template: '' };
      else if (request.url === '/api/chat') {
        requests++; const context = JSON.parse(JSON.parse(body).messages[1].content);
        const source = context.sources[0]; assert.ok(source);
        value = { done: true, done_reason: 'stop', message: { content: JSON.stringify({
          claims: [{ text: source.text, source_ids: [source.id] }],
          uncertainties: ['Synthetic response; no real inference.'], suggested_checks: [], changes }) } };
      } else { response.writeHead(404); response.end(); return; }
      response.setHeader('Content-Type', 'application/json'); response.end(JSON.stringify(value));
    });
  });
  const command = async (suffix: string) => { await vscode.commands.executeCommand('thread.'+suffix); assert.equal(picks.length, 0); assert.equal(prompts.length, 0); };
  const review = async (...choices: string[]) => { picks.push(...choices); await command('review'); };
  const feature = async (next: any[]) => { changes = next; prompts.push('Change value in app.py'); await command('feature'); assert.ok(agent.result.proposal); };
  const unchanged = (text: string) => assert.equal(readFileSync(app, 'utf8'), text);
  try {
    if (process.env.THREAD_TEST_PHASE === 'resume') {
      // A second real extension host uses the same isolated profile/workspace storage.
      await review('apply', 'pause');
      assert.equal(agent.result.decision, 'pending'); assert.equal(approvals, 0);
      unchanged('value = 2\n');
      await review('cancel'); assert.equal(agent.result.decision, 'cancelled');
      console.log('THREAD_WINDOWS_RELOAD_PASSED: actual second activation retained proposal but required fresh diff review');
      return;
    }
    await new Promise<void>((resolve, reject) => { server.once('error', reject); server.listen(11434, '127.0.0.1', resolve); });
    picks.push('fixture:local'); await command('setup');
    assert.equal(agent.detectedPython.bundled, true);
    assert.equal(realpathSync(agent.detectedPython.executable), realpathSync(path.join(extension.extensionPath, 'native/win32-x64/thread-backend/thread-backend.exe')));
    assert.equal(vscode.workspace.getConfiguration('thread').inspect<string>('model')!.globalValue, 'fixture:local');
    await vscode.window.showTextDocument(await vscode.workspace.openTextDocument(app));
    await feature([{ path: 'app.py', old_text: 'value = 1', new_text: 'value = 2' }]);
    unchanged('value = 1\n');
    await review('pause'); assert.equal(agent.result.decision, 'pending'); unchanged('value = 1\n');
    await review('apply', 'pause'); assert.equal(approvals, 0); unchanged('value = 1\n');
    await review('cancel'); assert.equal(agent.result.decision, 'cancelled'); unchanged('value = 1\n');
    await feature([{ path: 'app.py', old_text: 'value = 1', new_text: 'value = 2' }]);
    // Actual editor dirty buffer must reject application before dispatching an edit.
    const document = await vscode.workspace.openTextDocument(app);
    const dirty = new vscode.WorkspaceEdit(); dirty.insert(document.uri, new vscode.Position(0, 0), '# dirty\n');
    await vscode.workspace.applyEdit(dirty);
    await review('diff', 'file', 'apply'); assert.ok(errors.pop()!.includes('Save or revert'));
    unchanged('value = 1\n');
    await vscode.window.showTextDocument(document);
    await vscode.commands.executeCommand('workbench.action.files.revert');
    assert.equal(document.isDirty, false);
    // Disk changes invalidate the native proposal without dispatching an editor edit.
    writeFileSync(app, 'value = 3\n');
    await review('diff', 'file', 'apply'); assert.ok(errors.pop()!.includes('changed'));
    unchanged('value = 3\n');
    await command('clear'); writeFileSync(app, 'value = 1\n');
    await feature([{ path: 'app.py', old_text: 'value = 1', new_text: 'value = 2' },
      { path: 'new.py', old_text: '', new_text: 'created = True\n' }]);
    // Review both exact native diffs; scripted explicit modal approval.
    const savedPicker = installedAPI.window.showQuickPick;
    let fileIndex = 0;
    installedAPI.window.showQuickPick = async (items: any[]) => {
      if (picks[0] === 'file') { picks.shift(); return items[fileIndex++]; }
      return savedPicker(items);
    };
    await review('diff', 'file', 'diff', 'file', 'apply');
    installedAPI.window.showQuickPick = savedPicker;
    assert.equal(agent.result.decision, 'applied');
    const edited = await vscode.workspace.openTextDocument(app);
    assert.equal(edited.getText(), 'value = 2\n'); assert.equal(edited.isDirty, true); unchanged('value = 1\n');
    const created = await vscode.workspace.openTextDocument(path.join(root, 'new.py'));
    assert.equal(created.getText(), 'created = True\n');
    await command('review'); assert.ok(errors.pop()!.includes('no pending proposal'));
    await edited.save(); await created.save();
    assert.ok(requests >= 3); assert.ok(diffConfirmations >= 4); assert.equal(errors.length, 0);
    await command('clear');
    await feature([{ path: 'app.py', old_text: 'value = 2', new_text: 'value = 4' }]);
    await review('diff', 'file', 'pause'); unchanged('value = 2\n');
    console.log('THREAD_WINDOWS_POSITIVE_PASSED: installed native setup/inventory, real commands, pause/cancel, dirty/stale rejection, reviewed replacement/creation, unsaved existing buffer, duplicate rejection');
    console.log('LIMITS: synthetic provider and scripted approvals; no real runtime/model, ordinary-user or Windows ARM certification');
  } finally {
    Agent.prototype.setup = original.setup; Agent.prototype.review = original.review;
    Object.assign(installedAPI.window, { showQuickPick: original.pick, showInputBox: original.input,
      showInformationMessage: original.info, showWarningMessage: original.warning, showErrorMessage: original.error });
    if (server.listening) await new Promise<void>(resolve => server.close(() => resolve()));
  }
}
