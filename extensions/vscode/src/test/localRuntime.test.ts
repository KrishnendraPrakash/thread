import { test } from 'node:test';
import * as assert from 'node:assert/strict';
import * as http from 'node:http';
import * as net from 'node:net';
import { localEndpoint, ollamaJson, pullModel } from '../localRuntime';

test('managed inference rejects remote and credential-bearing endpoints', () => {
  for (const value of ['https://127.0.0.1', 'http://localhost', 'http://example.com', 'http://user@127.0.0.1', 'http://127.0.0.1/x']) {
    assert.throws(() => localEndpoint(value));
  }
  assert.equal(localEndpoint('http://127.0.0.1:34567').port, '34567');
});

test('model pull requires final success, reports progress and supports cancellation', async () => {
  let reply = '{"status":"pulling","total":10,"completed":5}\n{"status":"success"}\n';
  const server = http.createServer((request, response) => {
    response.setHeader('Content-Type', 'application/json');
    if (request.url === '/api/version') { response.end('{"version":"fixture"}'); return; }
    if (reply === 'hang') { response.write('{"status":"pulling"}\n'); return; }
    response.end(reply);
  });
  await new Promise<void>(resolve => server.listen(0, '127.0.0.1', resolve));
  const endpoint = `http://127.0.0.1:${(server.address() as net.AddressInfo).port}`;
  try {
    assert.equal((await ollamaJson(endpoint, '/api/version')).version, 'fixture');
    const progress: string[] = [];
    await pullModel(endpoint, 'qwen2.5-coder:1.5b', new AbortController().signal, message => progress.push(message));
    assert.ok(progress.some(value => value.includes('50%')));
    reply = '{"status":"pulling"}\n';
    await assert.rejects(pullModel(endpoint, 'qwen2.5-coder:1.5b', new AbortController().signal, () => {}), /did not complete/);
    reply = '{"error":"fixture disk full"}\n';
    await assert.rejects(pullModel(endpoint, 'qwen2.5-coder:1.5b', new AbortController().signal, () => {}), /disk full/);
    await assert.rejects(pullModel(endpoint, 'unknown:model', new AbortController().signal, () => {}), /listed starter/);
    reply = 'hang';
    const controller = new AbortController();
    await assert.rejects(pullModel(endpoint, 'qwen2.5-coder:1.5b', controller.signal, () => controller.abort()), /abort/i);
  } finally { server.closeAllConnections(); await new Promise<void>(resolve => server.close(() => resolve())); }
});
