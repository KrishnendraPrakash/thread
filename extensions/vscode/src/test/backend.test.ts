import { test } from 'node:test';
import * as assert from 'node:assert/strict';
import { mkdtemp, mkdir, writeFile, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import * as path from 'node:path';
import { Backend, BACKEND_TARGETS, bundledBackend, backendArguments } from '../backend';

test('native backend selection is bounded to the six packaging targets', async () => {
  const folder = await mkdtemp(path.join(tmpdir(), 'thread-native-test-'));
  try {
    assert.equal(bundledBackend(folder), undefined);
    for (const target of BACKEND_TARGETS) {
      const [platform, arch] = target.split('-');
      const executable = path.join(folder, 'native', target, 'thread-backend', platform === 'win32' ? 'thread-backend.exe' : 'thread-backend');
      await mkdir(path.dirname(executable), { recursive: true });
      await writeFile(executable, 'fixture, never executed');
      assert.equal(bundledBackend(folder, platform, arch), executable);
    }
    assert.equal(bundledBackend(folder, 'win32', 'ia32'), undefined);
    assert.deepEqual(backendArguments(bundledBackend(folder)!, folder), []);
    assert.deepEqual(backendArguments('python3', folder), ['-I', '-u', path.join(folder, 'python', 'bridge.py')]);
  } finally { await rm(folder, { recursive: true, force: true }); }
});

test('packaged executable uses the JSON protocol without Python flags', { skip: process.platform === 'win32' }, async () => {
  const folder = await mkdtemp(path.join(tmpdir(), 'thread-native-launch-'));
  try {
    const executable = path.join(folder, 'native', `${process.platform}-${process.arch}`, 'thread-backend', 'thread-backend');
    await mkdir(path.dirname(executable), { recursive: true });
    await writeFile(executable, '#!/bin/sh\nif [ "$#" -ne 0 ]; then exit 3; fi\nread request\nprintf \'{"ok":true,"result":{"packaged":true}}\\n\'\n', { mode: 0o755 });
    assert.deepEqual(await new Backend().call(executable, folder, { operation: 'python' }), { packaged: true });
  } finally { await rm(folder, { recursive: true, force: true }); }
});

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
