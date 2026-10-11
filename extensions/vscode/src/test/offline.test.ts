import { test } from 'node:test';
import * as assert from 'node:assert/strict';
import { mkdtemp, mkdir, writeFile, readFile, rm, readdir, symlink, link, stat } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import * as path from 'node:path';
import { createHash } from 'node:crypto';
import { inspectOffline, importOffline, OfflineManifest } from '../offline';

async function fixture(root: string): Promise<OfflineManifest> {
  const manifest: OfflineManifest = { schema: 1, target: `${process.platform}-${process.arch}`, runtimeExecutable: 'runtime/ollama', modelDirectory: 'models', model: 'fixture:tiny', runtimeVersion: '0.34.4', assets: [] };
  for (const [name, role] of [['backend/thread-backend', 'backend'], ['runtime/ollama', 'runtime'], ['models/blobs/fixture', 'model'], ['notices/LICENSE', 'notice']]) {
    const content = Buffer.from(role);
    await mkdir(path.dirname(path.join(root, name)), { recursive: true });
    await writeFile(path.join(root, name), content);
    manifest.assets.push({ path: name, role, size: content.length, sha256: createHash('sha256').update(content).digest('hex'), source: 'synthetic', license: 'test-only', version: 'fixture' });
  }
  await writeFile(path.join(root, 'bundle.json'), JSON.stringify(manifest));
  return manifest;
}

test('offline import verifies copied bytes and stages without executing assets', async () => {
  const root = await mkdtemp(path.join(tmpdir(), 'thread-offline-'));
  try {
    const source = path.join(root, 'source'); await mkdir(source);
    await fixture(source);
    const reviewed = await inspectOffline(source, `${process.platform}-${process.arch}`);
    const result = await importOffline(source, path.join(root, 'store'), reviewed.manifest.target, reviewed.digest, new AbortController().signal, () => {});
    assert.equal(await readFile(result.executable, 'utf8'), 'runtime');
    assert.equal(await readFile(path.join(result.models, 'blobs/fixture'), 'utf8'), 'model');
    assert.equal(createHash('sha256').update(await readFile(path.join(result.directory, 'bundle.json'))).digest('hex'), reviewed.digest);
    assert.equal(JSON.parse(await readFile(path.join(result.directory, 'import.json'), 'utf8')).manifestSha256, reviewed.digest);
    assert.deepEqual(await readdir(path.join(root, 'store')), [path.basename(result.directory)]);
  } finally { await rm(root, { recursive: true, force: true }); }
});

test('offline import preserves reviewed native helper execute flags', async () => {
  const root = await mkdtemp(path.join(tmpdir(), 'thread-offline-execute-'));
  try {
    const source = path.join(root, 'source'); await mkdir(source);
    const manifest = await fixture(source), content = Buffer.from('helper');
    await writeFile(path.join(source, 'runtime/llama-server'), content);
    manifest.assets.push({path:'runtime/llama-server', role:'runtime', size:content.length, sha256:createHash('sha256').update(content).digest('hex'), source:'synthetic', license:'test-only', version:'fixture', executable:true});
    await writeFile(path.join(source, 'bundle.json'), JSON.stringify(manifest));
    const reviewed = await inspectOffline(source, manifest.target);
    const result = await importOffline(source, path.join(root, 'store'), manifest.target, reviewed.digest, new AbortController().signal, () => {});
    if (process.platform !== 'win32') { assert.equal((await stat(path.join(result.directory, 'runtime/llama-server'))).mode & 0o111, 0o111); }
    manifest.assets[2].executable = true;
    await writeFile(path.join(source, 'bundle.json'), JSON.stringify(manifest));
    await assert.rejects(inspectOffline(source, manifest.target), /Executable flags/);
  } finally { await rm(root, {recursive:true, force:true}); }
});

test('offline import rejects mutation and removes incomplete staging', async () => {
  const root = await mkdtemp(path.join(tmpdir(), 'thread-offline-bad-'));
  try {
    const source = path.join(root, 'source'); await mkdir(source);
    const manifest = await fixture(source), store = path.join(root, 'store');
    const reviewed = await inspectOffline(source, manifest.target);
    await writeFile(path.join(source, 'models/blobs/fixture'), 'wrong');
    await assert.rejects(importOffline(source, store, manifest.target, reviewed.digest, new AbortController().signal, () => {}), /checksum/);
    assert.deepEqual(await readdir(store), []);
    manifest.model = 'changed'; await writeFile(path.join(source, 'bundle.json'), JSON.stringify(manifest));
    await assert.rejects(importOffline(source, store, manifest.target, reviewed.digest, new AbortController().signal, () => {}), /changed after review/);
  } finally { await rm(root, { recursive: true, force: true }); }
});

test('offline import rejects traversal, target mismatch, links and cancellation', async () => {
  const root = await mkdtemp(path.join(tmpdir(), 'thread-offline-policy-'));
  try {
    const source = path.join(root, 'source'); await mkdir(source);
    const manifest = await fixture(source), store = path.join(root, 'store');
    await assert.rejects(inspectOffline(source, 'not-a-target'), /Unsupported/);
    const reviewed = await inspectOffline(source, manifest.target);
    const controller = new AbortController(); controller.abort();
    await assert.rejects(importOffline(source, store, manifest.target, reviewed.digest, controller.signal, () => {}), /abort/i);
    manifest.assets[0].path = '../outside'; await writeFile(path.join(source, 'bundle.json'), JSON.stringify(manifest));
    await assert.rejects(inspectOffline(source, manifest.target), /Unsafe/);
    await fixture(source);
    await rm(path.join(source, 'runtime/ollama'));
    await link(path.join(source, 'models/blobs/fixture'), path.join(source, 'runtime/ollama'));
    await assert.rejects(importOffline(source, store, manifest.target, reviewed.digest, new AbortController().signal, () => {}), /unlinked/);
    await rm(path.join(source, 'runtime/ollama'));
    if (process.platform !== 'win32') {
      await symlink(path.join(source, 'models/blobs/fixture'), path.join(source, 'runtime/ollama'));
      await assert.rejects(importOffline(source, store, manifest.target, reviewed.digest, new AbortController().signal, () => {}), /links/);
    }
  } finally { await rm(root, { recursive: true, force: true }); }
});

test('offline imports serialize across callers and repeat imports preserve prior copies', async () => {
  const root = await mkdtemp(path.join(tmpdir(), 'thread-offline-concurrent-'));
  try {
    const source = path.join(root, 'source'); await mkdir(source); await fixture(source);
    const reviewed = await inspectOffline(source, `${process.platform}-${process.arch}`), store = path.join(root, 'store');
    const requests = await Promise.allSettled([0, 1].map(() => importOffline(source, store, reviewed.manifest.target, reviewed.digest, new AbortController().signal, () => {})));
    assert.equal(requests.filter(result => result.status === 'fulfilled').length, 1);
    const rejected = requests.find(result => result.status === 'rejected') as PromiseRejectedResult;
    assert.match(String(rejected.reason), /Another offline import/);
    const before = await readdir(store);
    const again = await importOffline(source, store, reviewed.manifest.target, reviewed.digest, new AbortController().signal, () => {});
    assert.equal((await readdir(store)).length, 2);
    assert.notEqual(path.basename(again.directory), before[0]);
    assert.equal(await readFile(path.join(store, before[0], 'runtime/ollama'), 'utf8'), 'runtime');
  } finally { await rm(root, { recursive: true, force: true }); }
});

test('partial-copy failure and cancellation release locks and preserve committed assets', async () => {
  const root = await mkdtemp(path.join(tmpdir(), 'thread-offline-partial-'));
  try {
    const source = path.join(root, 'source'); await mkdir(source); await fixture(source);
    const reviewed = await inspectOffline(source, `${process.platform}-${process.arch}`), store = path.join(root, 'store');
    const committed = await importOffline(source, store, reviewed.manifest.target, reviewed.digest, new AbortController().signal, () => {});
    await rm(path.join(source, 'models/blobs/fixture'));
    await assert.rejects(importOffline(source, store, reviewed.manifest.target, reviewed.digest, new AbortController().signal, () => {}), /ENOENT/);
    assert.deepEqual(await readdir(store), [path.basename(committed.directory)]);
    await fixture(source);
    const controller = new AbortController(); let progress = 0;
    await assert.rejects(importOffline(source, store, reviewed.manifest.target, reviewed.digest, controller.signal, () => { if (++progress === 2) { controller.abort(); } }), /abort/i);
    assert.deepEqual(await readdir(store), [path.basename(committed.directory)]);
    assert.equal(await readFile(committed.executable, 'utf8'), 'runtime');
  } finally { await rm(root, { recursive: true, force: true }); }
});

test('manifest rejects duplicate keys, reserved names and file/directory collisions', async () => {
  const root = await mkdtemp(path.join(tmpdir(), 'thread-offline-manifest-'));
  try {
    const source = path.join(root, 'source'); await mkdir(source);
    let manifest = await fixture(source);
    await writeFile(path.join(source, 'bundle.json'), JSON.stringify(manifest).replace('"schema":1', '"schema":1,"schema":1'));
    await assert.rejects(inspectOffline(source, manifest.target), /duplicate object keys/);
    for (const name of ['CON.txt', 'COM¹.txt', 'nested/<bad>', 'bundle.json/asset', 'import.json/asset']) {
      manifest = await fixture(source); manifest.assets[0].path = name;
      await writeFile(path.join(source, 'bundle.json'), JSON.stringify(manifest));
      await assert.rejects(inspectOffline(source, manifest.target), /Unsafe|conflict/);
    }
    manifest = await fixture(source);
    manifest.assets.push({ ...manifest.assets[0], path: manifest.assets[0].path + '/child' });
    await writeFile(path.join(source, 'bundle.json'), JSON.stringify(manifest));
    await assert.rejects(inspectOffline(source, manifest.target), /conflict/);
  } finally { await rm(root, { recursive: true, force: true }); }
});

test('cancelling during a streamed copy removes partial bytes and allows a later import', async () => {
  const root = await mkdtemp(path.join(tmpdir(), 'thread-offline-stream-'));
  try {
    const source = path.join(root, 'source'); await mkdir(source);
    const manifest = await fixture(source), content = Buffer.alloc(4 * 1024 * 1024, 42);
    await writeFile(path.join(source, manifest.assets[0].path), content);
    manifest.assets[0].size = content.length;
    manifest.assets[0].sha256 = createHash('sha256').update(content).digest('hex');
    await writeFile(path.join(source, 'bundle.json'), JSON.stringify(manifest));
    const reviewed = await inspectOffline(source, manifest.target), store = path.join(root, 'store');
    const controller = new AbortController(); let copied = false;
    await assert.rejects(importOffline(source, store, manifest.target, reviewed.digest, controller.signal, message => {
      if (message.startsWith('Copied')) { copied = true; controller.abort(); }
    }), /abort/i);
    assert.equal(copied, true);
    assert.deepEqual(await readdir(store), []);
    const complete = await importOffline(source, store, manifest.target, reviewed.digest, new AbortController().signal, () => {});
    assert.equal((await readFile(path.join(complete.directory, manifest.assets[0].path))).length, content.length);
  } finally { await rm(root, { recursive: true, force: true }); }
});
