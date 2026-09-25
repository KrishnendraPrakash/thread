import { test } from 'node:test';
import * as assert from 'node:assert/strict';
import { mkdtempSync, mkdirSync, writeFileSync, symlinkSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import * as path from 'node:path';
import { discoverPython, pythonCandidates } from '../python';

test('discovery skips stale, old and broken runtimes, accepts Python 3.9+', async () => {
  const seen: string[] = [];
  const result = await discoverPython(['/stale', '/old', '/broken', '/valid'], async candidate => {
    seen.push(candidate);
    if (candidate === '/stale') { throw new Error('ENOENT'); }
    if (candidate === '/broken') { throw new Error('missing bundled import'); }
    return { executable: candidate, version: candidate === '/old' ? '3.8.20' : '3.9.6' };
  });
  assert.equal(result.executable, '/valid'); assert.equal(seen.length, 4);
  for (const version of ['3.12.13', '3.14.3']) {
    assert.equal((await discoverPython(['/python'], async () => ({ executable: '/python', version }))).version, version);
  }
});

test('missing runtimes explain recovery; discovery is bounded and cancellable', async () => {
  await assert.rejects(discoverPython([], async () => { throw new Error('unused'); }), /Configure Python/);
  let count = 0;
  await assert.rejects(discoverPython(Array.from({ length: 20 }, (_, i) => `/${i}`), async () => {
    count++; throw new Error('bad runtime');
  }), /No working Python/);
  assert.equal(count, 12);
  count = 0;
  await assert.rejects(discoverPython(['/first', '/second'], async () => {
    count++; throw new Error('cancelled');
  }, () => count > 0), /discovery cancelled/);
  assert.equal(count, 1);
});

test('candidate discovery excludes repository executables, relative PATH and symlink aliases', () => {
  const root = mkdtempSync(path.join(tmpdir(), 'thread-python-'));
  try {
    const repo = path.join(root, 'repo'); const bin = path.join(root, 'bin');
    mkdirSync(repo); mkdirSync(bin);
    writeFileSync(path.join(repo, 'python3'), '', { mode: 0o755 });
    writeFileSync(path.join(bin, 'python3'), '', { mode: 0o755 });
    symlinkSync(path.join(repo, 'python3'), path.join(bin, 'python3.14'));
    symlinkSync(path.join(bin, 'python3'), path.join(bin, 'python3.12'));
    assert.deepEqual(pythonCandidates([repo, '.', 'relative/bin', bin].join(path.delimiter), [repo]), [path.join(bin, 'python3')]);
  } finally { rmSync(root, { recursive: true, force: true }); }
});
