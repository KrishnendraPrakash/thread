import { test } from 'node:test';
import * as assert from 'node:assert/strict';
import * as http from 'node:http';
import * as net from 'node:net';
import { localEndpoint, ollamaJson, runtimeSetupSupported } from '../localRuntime';

test('managed inference rejects remote and credential-bearing endpoints', () => {
  for (const value of ['https://127.0.0.1', 'http://localhost', 'http://example.com', 'http://user@127.0.0.1', 'http://127.0.0.1/x']) {
    assert.throws(() => localEndpoint(value));
  }
  assert.equal(localEndpoint('http://127.0.0.1:34567').port, '34567');
});

test('BYO setup rejects model downloads before any HTTP request', async () => {
  let requests = 0;
  const server = http.createServer((request, response) => { requests++; response.end('{"version":"fixture"}'); });
  await new Promise<void>(resolve => server.listen(0, '127.0.0.1', resolve));
  const endpoint = `http://127.0.0.1:${(server.address() as net.AddressInfo).port}`;
  try {
    await assert.rejects(ollamaJson(endpoint, '/api/pull', {model:'anything'}), /user-supplied/);
    await assert.rejects(ollamaJson(endpoint, '/api/pull?x=1', {model:'anything'}), /user-supplied/);
    assert.equal(requests, 0);
    assert.equal((await ollamaJson(endpoint, '/api/version')).version, 'fixture');
  } finally { server.closeAllConnections(); await new Promise<void>(resolve => server.close(() => resolve())); }
});

test('source profile retains Mac runtime acquisition without requiring a Linux native decoder', () => {
  assert.equal(runtimeSetupSupported(true, 'darwin', 'arm64', 23), true);
  assert.equal(runtimeSetupSupported(true, 'darwin', 'arm64', 22), false);
  assert.equal(runtimeSetupSupported(true, 'darwin', 'x64', 23), false);
  assert.equal(runtimeSetupSupported(true, 'linux', 'x64', 0), false);
  assert.equal(runtimeSetupSupported(true, 'linux', 'arm64', 0, true), true);
  assert.equal(runtimeSetupSupported(false, 'linux', 'x64', 0), true);
  assert.equal(runtimeSetupSupported(false, 'darwin', 'x64', 23), true);
});
