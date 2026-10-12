// Approved hosted CI only. Never invoke Ollama/model acquisition on a Mac.
const fs = require('node:fs');
const path = require('node:path');
const http = require('node:http');
const crypto = require('node:crypto');
const cp = require('node:child_process');
const assert = require('node:assert/strict');
const [phase, workArgument, target] = process.argv.slice(2);
if (!['install','run'].includes(phase) || !['win32-x64','linux-x64'].includes(target)
    || `${process.platform}-${process.arch}` !== target || process.env.GITHUB_ACTIONS !== 'true'
    || process.env.GITHUB_REPOSITORY !== 'KrishnendraPrakash/thread'
    || process.env.THREAD_RUNTIME_CI_ENVIRONMENT !== 'github-hosted' || process.env.RUNNER_ARCH !== 'X64') {
  throw Error('Real runtime/model work requires the approved hosted GitHub x64 runner.');
}
const work = path.resolve(workArgument);
const scope = JSON.parse(fs.readFileSync(path.join(work, 'owner-scope.json')));
assert.equal(scope.target, target); assert.equal(scope.runtime, '0.34.4');
const extension = path.resolve(__dirname, '..');
const directory = path.join(work, 'managed');
const ownedHome = path.join(work, 'runtime-home');
fs.mkdirSync(path.join(ownedHome, 'tmp'), {recursive:true});
const runtimeBinary = path.join(directory, 'ollama-0.34.4', process.platform === 'win32' ? 'ollama.exe' : 'bin/ollama');
// Delegate to the real spawn. Only the actual owned Ollama child receives a
// private home/temp; executable/arguments/loopback/cloud policy are unchanged.
const realSpawn = cp.spawn;
cp.spawn = function(executable, args, options) {
  if (path.resolve(executable) === path.resolve(runtimeBinary)) {
    options = {...options, env: {...options.env, HOME:ownedHome, USERPROFILE:ownedHome,
      TMPDIR:path.join(ownedHome,'tmp'), TMP:path.join(ownedHome,'tmp'), TEMP:path.join(ownedHome,'tmp')}};
  }
  return realSpawn.call(this, executable, args, options);
};
const {LocalRuntime, localEndpoint} = require('../out/localRuntime');
const {Backend, bundledBackend} = require('../out/backend');
const runtime = new LocalRuntime(directory);
const backend = new Backend();
const native = bundledBackend(extension);
assert.ok(native, 'Explicit host-native backend required; no Python fallback.');
const sha = data => crypto.createHash('sha256').update(data).digest('hex');
const record = (name, value) => { fs.writeFileSync(path.join(work,name),JSON.stringify(value,null,2)+'\n'); console.log(JSON.stringify({report:name,...value})); };
function request(endpoint, route, value, timeout=120000) {
  const base = localEndpoint(endpoint);
  return new Promise((resolve,reject) => {
    const body = value === undefined ? undefined : JSON.stringify(value);
    const req = http.request({hostname:'127.0.0.1',port:base.port,path:route,method:body?'POST':'GET',agent:false,
      headers:{'Content-Type':'application/json'},timeout}, res => {
      let chunks=[],bytes=0;
      res.on('data',chunk=>{bytes+=chunk.length;if(bytes>4*1024*1024){req.destroy(Error('Response bound'));return;}chunks.push(chunk);});
      res.on('error',reject);res.on('end',()=>{
        try {assert.equal(res.statusCode,200);resolve(JSON.parse(Buffer.concat(chunks).toString('utf8')));}catch(error){reject(error);}
      });
    });
    req.on('timeout',()=>req.destroy(Error('Bounded request timeout')));req.on('error',reject);req.end(body);
  });
}
function ownedProcesses() {
  const prefix = fs.realpathSync.native(work)+path.sep;
  if (process.platform === 'win32') {
    const script = "Get-CimInstance Win32_Process | Where-Object { $_.ExecutablePath -and $_.ExecutablePath.StartsWith($env.THREAD_OWNED_TEST_ROOT,[StringComparison]::OrdinalIgnoreCase) } | Select-Object ProcessId,ExecutablePath | ConvertTo-Json -Compress";
    const text = cp.execFileSync('powershell.exe',['-NoProfile','-NonInteractive','-Command',script],
      {encoding:'utf8',timeout:30000,env:{...process.env,THREAD_OWNED_TEST_ROOT:prefix}}).trim();
    return text ? [].concat(JSON.parse(text)).map(item=>({pid:item.ProcessId,executable:item.ExecutablePath})) : [];
  }
  return fs.readdirSync('/proc').filter(name=>/^\d+$/.test(name)).flatMap(name=>{
    try {const executable=fs.readlinkSync('/proc/'+name+'/exe');return executable.startsWith(prefix)?[{pid:Number(name),executable}]:[];}catch{return [];}
  });
}
async function cleanup(endpoint, proxy) {
  if(endpoint) {try {await request(endpoint,'/api/generate',{model:scope.model,keep_alive:0},5000);}catch{}}
  backend.cancel();
  if(proxy) {proxy.closeAllConnections();await new Promise(resolve=>proxy.close(resolve));}
  runtime.stop();
  await new Promise(resolve=>setTimeout(resolve,500));
  for(const process of ownedProcesses()) {
    if(target==='win32-x64') cp.execFileSync('taskkill.exe',['/PID',String(process.pid),'/T','/F'],{timeout:30000,stdio:'ignore'});
    else {try {global.process.kill(process.pid,'SIGKILL');}catch(error){if(error.code!=='ESRCH')throw error;}}
  }
  await new Promise(resolve=>setTimeout(resolve,500));
  assert.deepEqual(ownedProcesses(),[], 'No owned runtime/runner process may remain.');
  record('cleanup.json',{owned_processes_remaining:0,only_owned_paths_targeted:true});
}
async function main() {
  if(phase==='install') {
    const signal=AbortSignal.timeout(12*60*1000);
    await runtime.install(native,extension,signal,message=>console.log(message));
    assert.equal(runtime.installed,true);
    record('installation.json',{target,runtime:'0.34.4',actual_native_installer:true,executed_ollama:false});
    return;
  }
  assert.equal(JSON.parse(fs.readFileSync(path.join(work,'vendor-audit.json'))).status,'ready_for_private_test');
  assert.equal(JSON.parse(fs.readFileSync(path.join(work,'model-acquisition.json'))).manifest_sha256,scope.manifest_sha256);
  let endpoint,proxy;
  const wire=[];
  try {
    endpoint=await runtime.start(AbortSignal.timeout(30000));
    assert.equal((await request(endpoint,'/api/version')).version,'0.34.4');
    const models=await backend.call(native,extension,{operation:'models',endpoint});
    assert.ok(models.models.includes(scope.model));
    const metadata=await request(endpoint,'/api/show',{model:scope.model});
    assert.equal(metadata.details.quantization_level,'Q4_K_M');
    const smoke=await request(endpoint,'/api/chat',{model:scope.model,stream:false,
      messages:[{role:'user',content:'Respond with READY.'}],format:{type:'object',properties:{answer:{type:'string',enum:['READY']}},required:['answer'],additionalProperties:false},
      options:{temperature:0,seed:0,num_ctx:1024,num_predict:32,num_gpu:0},keep_alive:'5m'});
    assert.equal(smoke.done,true);assert.ok(smoke.message.content.trim());
    const residency=await request(endpoint,'/api/ps');
    assert.ok(residency.models.length);assert.ok(residency.models.every(model=>model.size_vram===0));
    record('smoke.json',{target,runtime:'0.34.4',model:scope.model,completion:true,cpu_residency:true,
      output:smoke.message.content,done_reason:smoke.done_reason,eval_count:smoke.eval_count,
      model_quality_certified:false,external_network_denial_certified:false});
    const base=localEndpoint(endpoint);
    proxy=http.createServer((incoming,outgoing)=>{
      let body=[],bytes=0;
      incoming.on('data',chunk=>{bytes+=chunk.length;if(bytes>2*1024*1024){incoming.destroy();return;}body.push(chunk);});
      incoming.on('end',()=>{
        if(!['/api/tags','/api/show','/api/version','/api/chat'].includes(incoming.url)){outgoing.writeHead(404);outgoing.end();return;}
        const original=Buffer.concat(body);
        const forward=http.request({hostname:'127.0.0.1',port:base.port,path:incoming.url,method:incoming.method,agent:false,
          headers:{'Content-Type':'application/json'},timeout:600000}, response=>{
          let chunks=[],count=0;
          response.on('data',chunk=>{count+=chunk.length;if(count>4*1024*1024){forward.destroy(Error('Wire bound'));return;}chunks.push(chunk);});
          response.on('end',()=>{
            const raw=Buffer.concat(chunks);
            if(incoming.url==='/api/chat') wire.push({request_sha256:sha(original),request_utf8:original.toString('utf8'),
              response_sha256:sha(raw),response_utf8:raw.toString('utf8'),http_status:response.statusCode});
            outgoing.writeHead(response.statusCode,{'Content-Type':'application/json'});outgoing.end(raw);
          });
          response.on('error',error=>outgoing.destroy(error));
        });
        forward.on('timeout',()=>forward.destroy(Error('Wire timeout')));forward.on('error',error=>outgoing.destroy(error));forward.end(original);
      });
    });
    await new Promise(resolve=>proxy.listen(0,'127.0.0.1',resolve));
    const source=path.join(work,'source');fs.mkdirSync(source);
    const file=path.join(source,'app.py'),text='def add(a, b):\n    return a + b\n';fs.writeFileSync(file,text);
    const requestValue={operation:'run',mode:'ask',prompt:'What does add return?',root:source,model:scope.model,
      endpoint:'http://127.0.0.1:'+proxy.address().port};
    let result,error;
    try {result=await backend.call(native,extension,requestValue,650000);}catch(failure){error=String(failure.message);}
    assert.equal(fs.readFileSync(file,'utf8'),text);assert.deepEqual(fs.readdirSync(source),['app.py']);
    assert.equal(wire.length,1,'One unchanged production chat request must reach the real runtime.');
    const response=JSON.parse(wire[0].response_utf8);
    record('production-structured-request.json',{native_request:requestValue,wire,
      backend_accepted:!!result,backend_error:error,result,source_unchanged:true,
      done:response.done,done_reason:response.done_reason,eval_count:response.eval_count,
      semantic_verification:'not_performed',release_gate_passed:false});
    const after=await request(endpoint,'/api/ps');assert.ok(after.models.every(model=>model.size_vram===0));
    console.log('THREAD_REAL_RUNTIME_INTEGRATION_COMPLETED: '+target+'; structured acceptance recorded separately from smoke and model quality');
  } finally {await cleanup(endpoint,proxy);}
}
main().catch(error=>{console.error(error);process.exitCode=1;});
