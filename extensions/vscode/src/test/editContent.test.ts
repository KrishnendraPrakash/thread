import { test } from 'node:test';
import * as assert from 'node:assert/strict';
import Module = require('node:module');

test('reviewed content selects exact editor line endings and rejects normalization before dispatch', () => {
  const loader = Module as unknown as { _load: (...args: any[]) => any };
  const original = loader._load;
  try {
    loader._load = function (name: string, ...args: any[]): any {
      return name === 'vscode' ? { EndOfLine: { LF: 1, CRLF: 2 } } : original.call(this, name, ...args);
    };
    const { proposalLineEnding } = require('../extension');
    assert.equal(proposalLineEnding('one\ntwo\n'), 1);
    assert.equal(proposalLineEnding('one\r\ntwo\r\n'), 2);
    assert.equal(proposalLineEnding('one'), undefined);
    for (const text of ['one\r\ntwo\n', 'one\ntwo\r\n', 'one\rtwo', 'one\r']) {
      assert.throws(() => proposalLineEnding(text), /no edit was dispatched/);
    }
  } finally { loader._load = original; }
});
