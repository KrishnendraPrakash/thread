import { test } from 'node:test';
import * as assert from 'node:assert/strict';
import * as http from 'node:http';
import * as net from 'node:net';
import { localEndpoint, ollamaJson } from '../localRuntime';

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
