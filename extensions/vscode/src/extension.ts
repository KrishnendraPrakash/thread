import * as vscode from 'vscode';
import * as path from 'node:path';
import { randomBytes } from 'node:crypto';
import { realpathSync } from 'node:fs';
import { Backend } from './backend';
import { Result, Mode, FileChange } from './types';

class Snapshots implements vscode.TextDocumentContentProvider {
  private values = new Map<string, string>();
  provideTextDocumentContent(uri: vscode.Uri): string { return this.values.get(uri.toString()) ?? 'Snapshot unavailable.'; }
  add(name: string, text: string): vscode.Uri {
    const uri = vscode.Uri.from({ scheme: 'thread-snapshot', path: '/' + name, query: randomBytes(8).toString('hex') });
    this.values.set(uri.toString(), text); return uri;
  }
  clear(): void { this.values.clear(); }
}

export function activate(context: vscode.ExtensionContext): void {
  const agent = new Agent(context);
  context.subscriptions.push(agent, vscode.workspace.registerTextDocumentContentProvider('thread-snapshot', agent.snapshots),
    vscode.window.registerWebviewViewProvider('thread.sidebar', agent));
  const commands: Record<string, () => unknown> = {
    setup: () => agent.setup(), ask: () => agent.request('ask'), debug: () => agent.request('debug'),
    feature: () => agent.request('feature'), summary: () => agent.request('summary'),
    review: () => agent.review(), cancel: () => agent.cancel(), clear: () => agent.clear(),
    runTask: () => agent.runTask(),
  };
  for (const [name, callback] of Object.entries(commands)) {
    context.subscriptions.push(vscode.commands.registerCommand('thread.' + name, async () => {
      try { await callback(); } catch (error) { agent.error(error); }
    }));
  }
}

export class Agent implements vscode.WebviewViewProvider, vscode.Disposable {
  readonly snapshots = new Snapshots();
  private backend = new Backend();
  private view?: vscode.WebviewView;
  private result?: Result;
  private reviewing = false;
  private taskExecutions = new Set<vscode.TaskExecution>();
  private taskListener: vscode.Disposable;
  constructor(private context: vscode.ExtensionContext) {
    this.result = context.workspaceState.get<Result>('lastResult');
    if (this.result?.decision === 'applying') { this.result.decision = 'uncertain'; }
    this.taskListener = vscode.tasks.onDidEndTaskProcess(event => {
      if (this.taskExecutions.delete(event.execution)) {
        this.notify(`Task ended with exit code ${event.exitCode ?? 'unknown'}. Review terminal output; this is not proof the proposed change is correct.`);
      }
    });
  }
  dispose(): void { this.backend.cancel(); this.taskListener.dispose(); }
  private trusted(): void {
    if (!vscode.workspace.isTrusted) { throw new Error('Trust this workspace before using Thread.'); }
    if (process.platform === 'win32') { throw new Error('This experimental backend currently supports macOS and Linux.'); }
  }
  private setting(name: string, fallback: string): string {
    // A repository cannot choose which Python executable or model to run.
    return vscode.workspace.getConfiguration('thread').inspect<string>(name)?.globalValue ?? fallback;
  }
  private async call(request: object, python = this.setting('pythonPath', 'python3')): Promise<any> {
    this.trusted(); this.view?.webview.postMessage({ type: 'busy', value: true });
    try { return await this.backend.call(python, this.context.extensionPath, request); }
    finally { this.view?.webview.postMessage({ type: 'busy', value: false }); }
  }
  private async save(): Promise<void> {
    await this.context.workspaceState.update('lastResult', this.result);
    this.view?.webview.postMessage({ type: 'result', result: this.result });
  }
  notify(message: string): void {
    this.view?.webview.postMessage({ type: 'notice', message });
    void vscode.window.showInformationMessage(message);
  }
  error(error: unknown): void {
    const message = error instanceof Error ? error.message : String(error);
    this.view?.webview.postMessage({ type: 'notice', message });
    void vscode.window.showErrorMessage('Thread: ' + message);
  }
  private async configurePython(input: string): Promise<any> {
    const python = input.trim();
    if (!python || (!path.isAbsolute(python) && /[\\/]/.test(python))) {
      throw new Error('Enter an absolute Python executable path, or a command such as python3. Relative .venv paths are not supported.');
    }
    // Probe the exact user input before saving it. Do not reread a potentially stale setting.
    const runtime = await this.call({ operation: 'python' }, python);
    await vscode.workspace.getConfiguration('thread').update('pythonPath', python, vscode.ConfigurationTarget.Global);
    this.notify(`Python ${runtime.version} is ready at ${runtime.executable}. Checking local Ollama next.`);
    try { return await this.call({ operation: 'models' }, python); }
    catch (error) {
      throw new Error(`Python is ready at ${runtime.executable}, and its setting was saved. Local model setup failed: ${error instanceof Error ? error.message : String(error)} Install/start Ollama on this machine, then run Thread: Setup Local Model again.`);
    }
  }
  async setup(): Promise<void> {
    this.trusted();
    if (this.backend.busy) { throw new Error('Finish or cancel the current request before changing setup.'); }
    const python = await vscode.window.showInputBox({ title: 'Thread · Python 3.11+',
      prompt: 'Enter Python on THIS machine (absolute path recommended). This is separate from Python: Select Interpreter. Python itself and Ollama are not bundled.',
      value: this.setting('pythonPath', 'python3'), ignoreFocusOut: true });
    if (!python?.trim()) { return; }
    const result = await this.configurePython(python);
    if (!result.models.length) { throw new Error('No local Ollama models found. Install a text model separately, then run Setup again.'); }
    const chosen = await vscode.window.showQuickPick(result.models as string[], {
      title: 'Thread · Choose an installed local Ollama model',
      placeHolder: 'Choose a coding-capable text model. No model is a certified default.', ignoreFocusOut: true,
    });
    if (chosen) {
      await vscode.workspace.getConfiguration('thread').update('model', chosen, vscode.ConfigurationTarget.Global);
      this.notify(`Using ${chosen} at 127.0.0.1:11434. No paid API key is required.`);
    }
  }
  private async folder(): Promise<vscode.WorkspaceFolder | undefined> {
    const folders = vscode.workspace.workspaceFolders?.filter(folder => folder.uri.scheme === 'file') ?? [];
    if (!folders.length) { throw new Error('Open a local repository folder in VS Code first.'); }
    return folders.length === 1 ? folders[0] : vscode.window.showWorkspaceFolderPick({ placeHolder: 'Choose the repository to inspect' });
  }
  private dirty(root: string): boolean {
    return vscode.workspace.textDocuments.some(document => document.isDirty && document.uri.scheme === 'file'
      && contained(realpathSync(root), realpathSync(document.uri.fsPath)));
  }
  async request(mode: Mode, supplied?: string): Promise<void> {
    this.trusted();
    if (this.backend.busy || this.reviewing) { throw new Error('Finish or cancel the current request/review first.'); }
    if (this.result?.proposal && this.result.decision === 'pending') {
      const replace = await vscode.window.showWarningMessage('Starting a new request replaces the saved pending proposal.', { modal: true }, 'Replace proposal');
      if (replace !== 'Replace proposal') { return; }
      this.result.decision = 'cancelled'; await this.save();
    }
    const folder = await this.folder(); if (!folder) { return; }
    const model = this.setting('model', '');
    if (!model) { await this.setup(); return; }
    const prompt = supplied?.trim() || await vscode.window.showInputBox({ title: `Thread · ${mode}`,
      prompt: mode === 'debug' ? 'Describe the failure or paste its error. Saved-file VS Code diagnostics are included.' : 'Describe what you want to understand, build or summarize.',
      ignoreFocusOut: true, validateInput: value => Buffer.byteLength(value) > 2500 ? 'Use at most 2,500 UTF-8 bytes.' : undefined });
    if (!prompt?.trim()) { return; }
    const request: Record<string, unknown> = { operation: 'run', mode, prompt, model, root: folder.uri.fsPath };
    if (mode === 'summary') {
      const files = await vscode.window.showOpenDialog({ canSelectMany: false, title: 'Choose a document to send to your local model',
        filters: { 'Supported documents': ['txt', 'md', 'rst', 'csv', 'log', 'json', 'yaml', 'yml', 'toml', 'pdf', 'docx'] } });
      if (!files?.[0] || files[0].scheme !== 'file') { return; }
      const selection = await vscode.window.showInputBox({ title: 'Thread · Document scope', value: '', ignoreFocusOut: true,
        prompt: 'Leave blank for all text, or enter 1-10: PDF pages, DOCX paragraphs, or text lines. Large documents need a range.' });
      if (selection === undefined) { return; }
      request.document = files[0].fsPath; request.selection = selection;
    } else {
      if (this.dirty(folder.uri.fsPath)) { throw new Error('Save or revert workspace edits first. Thread analyzes saved files only.'); }
      const active = vscode.window.activeTextEditor?.document.uri;
      if (active?.scheme === 'file' && contained(folder.uri.fsPath, active.fsPath)) {
        request.active = path.relative(folder.uri.fsPath, active.fsPath).split(path.sep).join('/');
      }
      if (mode === 'debug') {
        request.diagnostics = vscode.languages.getDiagnostics().filter(([uri]) => uri.scheme === 'file' && contained(folder.uri.fsPath, uri.fsPath))
          .flatMap(([uri, entries]) => entries.slice(0, 8).map(diagnostic =>
            `${path.relative(folder.uri.fsPath, uri.fsPath)}:${diagnostic.range.start.line + 1}: ${diagnostic.message}`)).join('\n').slice(0, 2500);
      }
    }
    await vscode.commands.executeCommand('thread.sidebar.focus');
    this.result = await this.call(request) as Result;
    await this.save();
    this.notify(this.result.proposal ? 'Analysis ready. Review the proposed diffs before applying changes.' : 'Analysis ready in the Thread sidebar.');
  }
  cancel(): void { this.backend.cancel(); }
  async clear(): Promise<void> {
    if (this.reviewing) { throw new Error('Finish the current review first.'); }
    this.cancel(); this.result = undefined; this.snapshots.clear(); await this.save();
    this.notify('Saved analysis, source snapshots and pending proposal cleared from this workspace’s extension storage.');
  }
  async review(): Promise<void> {
    this.trusted();
    if (this.reviewing || this.backend.busy) { throw new Error('A request or review is already active.'); }
    const result = this.result, proposal = result?.proposal;
    if (!result || !proposal || result.decision !== 'pending') { throw new Error('There is no pending proposal. Applied, cancelled or uncertain proposals cannot be reused.'); }
    if (!vscode.workspace.workspaceFolders?.some(folder => realpathSync(folder.uri.fsPath) === proposal.root)) { throw new Error('Open the proposal’s original workspace.'); }
    this.reviewing = true;
    try {
      const reviewed = new Set<string>();
      while (result.decision === 'pending') {
        const options = [
          { label: 'Review a diff (recommended)', description: 'Inspect the exact before/after content before approval.', key: 'diff' },
          { label: 'Apply to editor buffers', description: `Requires every diff reviewed (${reviewed.size}/${proposal.files.length}). Save and test afterward.`, key: 'apply' },
          { label: 'Refine with my own instructions', description: 'Write an explicit request for a new proposal.', key: 'custom' },
          { label: 'More options', description: 'Inspect sources or suggested checks.', key: 'more' },
          { label: 'Pause review', description: 'Keep the proposal for later; no changes.', key: 'pause' },
          { label: 'Cancel proposal', description: 'Invalidate this proposal; no changes.', key: 'cancel' },
        ];
        const choice = await vscode.window.showQuickPick(options, { title: 'Thread · Human review', ignoreFocusOut: true });
        if (!choice || choice.key === 'pause') { break; }
        if (choice.key === 'cancel') { result.decision = 'cancelled'; await this.save(); break; }
        if (choice.key === 'more') {
          const uri = this.snapshots.add('evidence-and-checks.json', JSON.stringify({ sources: result.sources, checks: result.answer.suggested_checks, limits: result.answer.uncertainties }, null, 2));
          await vscode.window.showTextDocument(uri); continue;
        }
        if (choice.key === 'custom') {
          const custom = await vscode.window.showInputBox({ title: 'Thread · Explicit refinement', prompt: 'Describe exactly what to change. This requests a new proposal, not approval.', ignoreFocusOut: true });
          if (custom?.trim()) {
            result.decision = 'cancelled'; await this.save(); this.reviewing = false;
            await this.request(result.mode, result.prompt + '\nRefinement: ' + custom); return;
          } continue;
        }
        if (choice.key === 'diff') {
          const picked = await vscode.window.showQuickPick(proposal.files.map(file => ({ label: file.path, file })), { title: 'Choose a file to review', ignoreFocusOut: true });
          if (picked) {
            const file = picked.file;
            await vscode.commands.executeCommand('vscode.diff', this.snapshots.add('before/' + file.path, file.before ?? ''),
              this.snapshots.add('after/' + file.path, file.after), `Thread proposal · ${file.path}`);
            reviewed.add(file.path);
            // Return control so the human can actually read the diff before reopening review.
            this.notify('Inspect the diff. Choose Reviewed this diff to continue or Pause to return later.');
            // Review all files in this invocation through a confirmation after inspection.
            const next = await vscode.window.showInformationMessage(`Inspect ${file.path}, then confirm when ready.`, 'Reviewed this diff', 'Pause');
            if (next !== 'Reviewed this diff') { break; }
          } continue;
        }
        if (choice.key === 'apply') {
          if (reviewed.size !== proposal.files.length) { this.notify('Review every diff in this review session before applying.'); continue; }
          const confirm = await vscode.window.showWarningMessage(`Apply this exact proposal to ${proposal.files.length} editor file(s)? New files may be created on disk. Existing edits remain unsaved. No tests have run.`, { modal: true }, 'Apply reviewed changes');
          if (confirm !== 'Apply reviewed changes') { continue; }
          await this.apply(result); break;
        }
      }
    } finally { this.reviewing = false; }
  }
  private fileUri(root: string, name: string): vscode.Uri {
    const folder = vscode.workspace.workspaceFolders?.find(item => item.uri.scheme === 'file' && realpathSync(item.uri.fsPath) === root);
    if (!folder) { throw new Error('The original workspace is no longer open.'); }
    const uri = vscode.Uri.joinPath(folder.uri, name);
    if (!contained(folder.uri.fsPath, uri.fsPath)) { throw new Error('Edit path escaped the workspace.'); }
    return uri;
  }
  private async apply(result: Result): Promise<void> {
    const proposal = result.proposal!;
    if (result !== this.result || result.decision !== 'pending') { throw new Error('This proposal is no longer pending.'); }
    result.trace?.push({ type: 'human_decision', proposal_id: proposal.id, decision: 'apply_reviewed_changes', at: new Date().toISOString() });
    if (this.dirty(proposal.root)) { throw new Error('Save or revert all workspace edits before applying.'); }
    await this.call({ operation: 'validate', root: proposal.root, proposal });
    const edit = new vscode.WorkspaceEdit();
    const opened: { file: FileChange; document: vscode.TextDocument; version: number }[] = [];
    for (const file of proposal.files) {
      const uri = this.fileUri(proposal.root, file.path);
      if (file.before === null) { edit.createFile(uri, { overwrite: false, ignoreIfExists: false }); edit.insert(uri, new vscode.Position(0, 0), file.after); }
      else {
        const document = await vscode.workspace.openTextDocument(uri);
        if (document.isDirty || document.getText() !== file.before) { throw new Error('An edit target changed. Regenerate the proposal.'); }
        opened.push({ file, document, version: document.version });
        edit.replace(uri, new vscode.Range(document.positionAt(0), document.positionAt(document.getText().length)), file.after);
      }
    }
    result.decision = 'applying'; await this.save();
    // Validate again after editor loading and persistence, then check buffers synchronously.
    try {
      await this.call({ operation: 'validate', root: proposal.root, proposal });
      if (opened.some(item => item.document.isDirty || item.document.version !== item.version || item.document.getText() !== item.file.before)) {
        throw new Error('An editor buffer changed during approval. No edit was dispatched.');
      }
      const applied = await vscode.workspace.applyEdit(edit);
      if (!applied) { throw new Error('VS Code did not confirm the edit. Inspect files before retrying with a new proposal.'); }
      for (const file of proposal.files) {
        const document = await vscode.workspace.openTextDocument(this.fileUri(proposal.root, file.path));
        if (document.getText() !== file.after) { throw new Error('Post-edit content differs from the proposal. Inspect files; do not blindly retry.'); }
      }
      result.decision = 'applied'; result.status = 'Approved proposal applied to editor buffers. Save, inspect and run checks; correctness is unverified.';
      await this.save(); this.notify(result.status);
    } catch (error) { result.decision = 'uncertain'; await this.save(); throw error; }
  }
  async runTask(): Promise<void> {
    this.trusted();
    const tasks = await vscode.tasks.fetchTasks();
    const selected = await vscode.window.showQuickPick(tasks.map(task => ({ label: task.name, description: task.source, task })), { title: 'Thread · Choose an existing workspace task', ignoreFocusOut: true });
    if (!selected) { return; }
    const execution = selected.task.execution;
    if (!(execution instanceof vscode.ShellExecution) && !(execution instanceof vscode.ProcessExecution)) { throw new Error('Custom task executions are not supported by this review UI. Use VS Code’s task UI directly.'); }
    const details = execution instanceof vscode.ShellExecution ? execution.commandLine ?? JSON.stringify({ command: execution.command, args: execution.args }) : JSON.stringify({ process: execution.process, args: execution.args });
    const choice = await vscode.window.showWarningMessage(`Run task “${selected.task.name}”?\n${details}\nWorking directory: ${execution.options?.cwd ?? 'workspace default'}\nThis executes the task’s configured commands and dependencies with your permissions.`, { modal: true }, 'Run selected task');
    if (choice === 'Run selected task') { this.taskExecutions.add(await vscode.tasks.executeTask(selected.task)); }
  }
  resolveWebviewView(view: vscode.WebviewView): void {
    this.view = view; view.webview.options = { enableScripts: true, localResourceRoots: [vscode.Uri.joinPath(this.context.extensionUri, 'media')] };
    const nonce = randomBytes(20).toString('hex');
    const script = view.webview.asWebviewUri(vscode.Uri.joinPath(this.context.extensionUri, 'media', 'sidebar.js'));
    const style = view.webview.asWebviewUri(vscode.Uri.joinPath(this.context.extensionUri, 'media', 'sidebar.css'));
    view.webview.html = `<!doctype html><html><head><meta charset="UTF-8"><meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src ${view.webview.cspSource}; script-src 'nonce-${nonce}';"><meta name="viewport" content="width=device-width,initial-scale=1"><link rel="stylesheet" href="${style}"></head><body><h2>Thread</h2><p class="muted">Local model · Saved files · Human-reviewed edits</p><label for="mode">Workflow</label><select id="mode"><option value="ask">Ask about repository</option><option value="debug">Diagnose a problem</option><option value="feature">Propose a feature</option><option value="summary">Summarize a document</option></select><label for="prompt">Your request</label><textarea id="prompt" rows="5" placeholder="How does authentication work in this repository?"></textarea><div class="actions"><button id="run">Send</button><button id="cancel">Stop</button><button id="setup">Setup</button></div><p id="notice" role="status"></p><div id="output"></div><script nonce="${nonce}" src="${script}"></script></body></html>`;
    view.webview.onDidReceiveMessage(async message => {
      try {
        if (!message || typeof message.type !== 'string') { return; }
        if (message.type === 'ready') { view.webview.postMessage({ type: 'result', result: this.result }); view.webview.postMessage({ type: 'busy', value: this.backend.busy }); }
        else if (message.type === 'run' && ['ask', 'debug', 'feature', 'summary'].includes(message.mode) && typeof message.prompt === 'string' && Buffer.byteLength(message.prompt) <= 2500) { await this.request(message.mode, message.prompt); }
        else if (message.type === 'setup') { await this.setup(); }
        else if (message.type === 'cancel') { this.cancel(); }
        else if (message.type === 'review') { await this.review(); }
        else if (message.type === 'source' && typeof message.id === 'string') {
          const source = this.result?.sources.find(item => item.id === message.id);
          if (source) { await vscode.window.showTextDocument(this.snapshots.add(path.basename(source.path) + '.txt', JSON.stringify({ ...source }, null, 2))); }
        }
      } catch (error) { this.error(error); }
    }, undefined, this.context.subscriptions);
  }
}

export function contained(root: string, filename: string): boolean {
  const relative = path.relative(root, filename);
  return relative !== '' && !relative.startsWith('..' + path.sep) && relative !== '..' && !path.isAbsolute(relative);
}
