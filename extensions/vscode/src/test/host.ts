import * as vscode from 'vscode';
import * as assert from 'node:assert/strict';
import * as path from 'node:path';
import { Agent, contained } from '../extension';
import { Backend } from '../backend';

export async function run(): Promise<void> {
  const extension = vscode.extensions.getExtension('KrishnendraPrakash.thread-agent');
  assert.ok(extension); await extension.activate();
  const commands = await vscode.commands.getCommands(true);
  for (const name of ['setup', 'ask', 'debug', 'feature', 'summary', 'review', 'cancel', 'clear', 'runTask']) {
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
  const context = { extensionPath: extension.extensionPath, workspaceState: {
    get: (key: string) => states.get(key), update: async (key: string, value: any) => { states.set(key, structuredClone(value)); },
  } } as unknown as vscode.ExtensionContext;
  const agent: any = new Agent(context);
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
