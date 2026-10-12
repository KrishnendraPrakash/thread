import { test } from 'node:test';
import * as assert from 'node:assert/strict';
import Module = require('node:module');

test('Windows product guard rejects setup before invoking a backend', { skip: process.platform !== 'win32' }, async () => {
  const loader = Module as unknown as { _load: (...args: any[]) => any };
  const original = loader._load;
  try {
    loader._load = function (name: string, ...args: any[]): any {
      return name === 'vscode' ? { workspace: { isTrusted: true } } : original.call(this, name, ...args);
    };
    const { Agent } = require('../extension');
    let backendCalled = false;
    const fixture = { trusted: Agent.prototype.trusted, resolvePython: async () => { backendCalled = true; } };
    await assert.rejects(Agent.prototype.setup.call(fixture), /supports macOS and Linux/);
    assert.equal(backendCalled, false);
  } finally { loader._load = original; }
});
