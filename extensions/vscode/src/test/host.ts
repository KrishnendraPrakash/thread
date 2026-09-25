import * as vscode from 'vscode';
import * as assert from 'node:assert/strict';
import * as path from 'node:path';
import { Agent, contained } from '../extension';
import { Backend } from '../backend';

export async function run(): Promise<void> {
  const extension = vscode.extensions.getExtension('Krishnendra.thread-agent');
  assert.ok(extension); await extension.activate();
  const commands = await vscode.commands.getCommands(true);
  for (const name of ['setup', 'configurePython', 'ask', 'debug', 'feature', 'summary', 'review', 'cancel', 'clear', 'runTask']) {
    assert.ok(commands.includes('thread.' + name), 'Missing command ' + name);
  }
  await vscode.commands.executeCommand('thread.sidebar.focus');
  assert.equal(contained('/repo', '/repo2/file.py'), false);
  assert.equal(contained('/repo', '/repo/file.py'), true);
  const root = vscode.workspace.workspaceFolders![0].uri.fsPath;
  const python = path.resolve(extension.extensionPath, '../../.venv/bin/python');
  const backend = new Backend();
  // Build a real immutable proposal from the synthetic file without invoking a model.
  const { execFileSync } = await import('node:child_process');
  const script = 'import json,sys; from thread_agent.editor.workspace import Repository; from thread_agent.editor.proposals import proposal; r=Repository(sys.argv[1]); r.scan(); print(json.dumps(proposal(r,[{"path":"app.py","old_text":"value = 1","new_text":"value = 2"}],r.retrieve("value"))))';
  const proposal = JSON.parse(execFileSync(python, ['-c', script, root], { encoding: 'utf8' }));
  const result: any = { proposal, decision: 'pending', root };
  const states = new Map<string, any>();
  const context = { extensionPath: extension.extensionPath,
    globalStorageUri: vscode.Uri.file(path.join(root, 'extension-storage')),
    globalState: { get: (_key: string, fallback: unknown) => fallback, update: async () => {} }, workspaceState: {
    get: (key: string) => states.get(key), update: async (key: string, value: any) => { states.set(key, structuredClone(value)); },
  } } as unknown as vscode.ExtensionContext;
  const agent: any = new Agent(context);
  const config = vscode.workspace.getConfiguration('thread');
  const previousPython = config.inspect<string>('pythonPath')?.globalValue;
  const setupAgent: any = new Agent(context);
  setupAgent.notify = () => {};
  const calls: { python: string; operation: string }[] = [];
  setupAgent.backend = {
    busy: false, cancel: () => {},
    call: async (selected: string, folder: string, request: any) => {
      calls.push({ python: selected, operation: request.operation });
      if (request.operation === 'models') { throw new Error('Fixture: Ollama unavailable'); }
      return backend.call(selected, folder, request);
    },
  };
  try {
    await config.update('pythonPath', '/nonexistent/old-python', vscode.ConfigurationTarget.Global);
    // Simulate stale configuration reads during setup; both calls must use explicit input.
    setupAgent.setting = () => '/nonexistent/old-python';
    await assert.rejects(setupAgent.configurePython(python), /Python is ready.*setting was saved.*Ollama unavailable/);
    assert.deepEqual(calls, [{ python, operation: 'python' }, { python, operation: 'models' }]);
    assert.equal(config.inspect<string>('pythonPath')?.globalValue, python);
    const reloaded: any = new Agent(context);
    try { assert.equal(reloaded.setting('pythonPath', 'python3'), python); }
    finally { reloaded.dispose(); }
    await assert.rejects(setupAgent.configurePython('/nonexistent/new-python'), /Cannot start Python/);
    assert.equal(config.inspect<string>('pythonPath')?.globalValue, python);
    const count = calls.length;
    await assert.rejects(setupAgent.configurePython('.venv/bin/python'), /absolute Python/);
    assert.equal(calls.length, count);
    const automatic: any = new Agent(context);
    automatic.notify = () => {};
    automatic.backend = setupAgent.backend;
    automatic.setting = () => '/nonexistent/stale-python';
    let recovered = false;
    automatic.recoverModelSetup = async () => { recovered = true; };
    try {
      await automatic.setup();
      assert.equal(recovered, true);
      assert.ok(path.isAbsolute(automatic.detectedPython.executable));
      assert.notEqual(automatic.detectedPython.executable, '/nonexistent/stale-python');
      console.log(`THREAD_AUTODETECT_PASSED: ${automatic.detectedPython.version}; no Python input dialog, stale override recovered`);
    } finally { automatic.dispose(); }
    console.log('THREAD_SETUP_TESTS_PASSED: exact input despite stale settings, real Python probe, persistence despite missing Ollama, invalid path preserves settings, relative path rejection');
  } finally {
    setupAgent.dispose();
    await config.update('pythonPath', previousPython, vscode.ConfigurationTarget.Global);
  }
  agent.result = result; agent.notify = () => {};
  agent.call = (request: object) => backend.call(python, extension.extensionPath, request);
  try {
    await agent.apply(result); // Scripted fixture approval, never a real user authorization.
    const doc = await vscode.workspace.openTextDocument(path.join(root, 'app.py'));
    assert.equal(doc.getText(), 'value = 2\n'); assert.equal(doc.isDirty, true);
    assert.equal(result.decision, 'applied');
    await assert.rejects(agent.review(), /no pending proposal/);
    await doc.save();
    const createScript = 'import json,sys; from thread_agent.editor.workspace import Repository; from thread_agent.editor.proposals import proposal; r=Repository(sys.argv[1]); r.scan(); print(json.dumps(proposal(r,[{"path":"new.py","old_text":"","new_text":"created = True\\n"}],r.retrieve("value"))))';
    const next = { proposal: JSON.parse(execFileSync(python, ['-c', createScript, root], { encoding: 'utf8' })), decision: 'pending', root };
    agent.result = next;
    await agent.apply(next);
    const created = await vscode.workspace.openTextDocument(path.join(root, 'new.py'));
    assert.equal(created.getText(), 'created = True\n');
    assert.equal(next.decision, 'applied');
    await created.save();
    const stale = { proposal, decision: 'pending', root };
    agent.result = stale;
    await assert.rejects(agent.apply(stale), /changed/);
    assert.equal(doc.getText(), 'value = 2\n');
    // Native edit application, persistence, duplicate rejection and changed-source validation.
    assert.equal(states.get('lastResult').decision, 'applied');
    console.log('THREAD_HOST_TESTS_PASSED: activation, commands, scoped path, approved native edit and file creation, saved decision, duplicate and stale rejection, sidebar activation');
  } finally { agent.dispose(); }
}
