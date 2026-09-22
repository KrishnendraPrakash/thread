import { test } from 'node:test';
import * as assert from 'node:assert/strict';
import { mkdtemp, mkdir, writeFile, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import * as path from 'node:path';
import { Backend } from '../backend';

test('bridge rejects unknown operations without calling a model', async () => {
  const backend = new Backend();
  await assert.rejects(backend.call('python3', path.resolve(__dirname, '../..'), { operation: 'shell' }), /Unknown editor operation/);
  assert.equal(backend.busy, false);
});
test('spawn errors are surfaced and do not leave busy state', async () => {
  const backend = new Backend();
  await assert.rejects(backend.call('/nonexistent/thread-python', '/tmp', {}), /Cannot start Python/);
  assert.equal(backend.busy, false);
});
test('cancellation rejects late results and concurrent calls', async () => {
  const folder = await mkdtemp(path.join(tmpdir(), 'thread-bridge-test-'));
  try {
    await mkdir(path.join(folder, 'python'));
    await writeFile(path.join(folder, 'python/bridge.py'), 'import time\ntime.sleep(10)\nprint(\'{"ok":true,"result":{}}\')\n');
    const backend = new Backend();
    const pending = backend.call('python3', folder, {});
    await assert.rejects(backend.call('python3', folder, {}), /already running/);
    backend.cancel(); await assert.rejects(pending, /cancelled/); assert.equal(backend.busy, false);
  } finally { await rm(folder, { recursive: true, force: true }); }
});
