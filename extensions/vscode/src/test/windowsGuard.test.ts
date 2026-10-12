import { test } from 'node:test';
import * as assert from 'node:assert/strict';
import Module = require('node:module');
import * as fs from 'node:fs';
import * as os from 'node:os';
import * as path from 'node:path';

test('Windows product guard rejects setup before invoking a backend', { skip: process.platform !== 'win32' }, async () => {
  const loader = Module as unknown as { _load: (...args: any[]) => any };
  const original = loader._load;
  try {
    loader._load = function (name: string, ...args: any[]): any {
      return name === 'vscode' ? { workspace: { isTrusted: true } } : original.call(this, name, ...args);
    };
    const { Agent, workspacePath } = require('../extension');
    const folder = fs.mkdtempSync(path.join(os.tmpdir(), 'thread-identity-'));
    try {
      fs.mkdirSync(path.join(folder, 'other'));
      const alternateDrive = folder[0].toLowerCase() + folder.slice(1);
      assert.equal(workspacePath(alternateDrive), workspacePath(folder));
      assert.equal(workspacePath(folder), fs.realpathSync.native(folder));
      assert.notEqual(workspacePath(folder), workspacePath(path.join(folder, 'other')));
      assert.throws(() => workspacePath(path.join(folder, 'missing')));
    } finally { fs.rmSync(folder, { recursive: true, force: true }); }
    let backendCalled = false;
    const fixture = { trusted: Agent.prototype.trusted, resolvePython: async () => { backendCalled = true; } };
    await assert.rejects(Agent.prototype.setup.call(fixture), /supports macOS and Linux/);
    assert.equal(backendCalled, false);
  } finally { loader._load = original; }
});
