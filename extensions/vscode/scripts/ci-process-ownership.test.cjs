const test=require('node:test');
const assert=require('node:assert/strict');
const {ownedWindowsProcesses}=require('./ci-process-ownership.cjs');
const root='D:\\a\\_temp\\thread-runtime-integration';
test('system paths and sibling-prefix paths cannot authorize termination',()=>{
 const items=[
  {ProcessId:700,ExecutablePath:'C:\\Windows\\system32\\lsass.exe'},
  {ProcessId:701,ExecutablePath:root+'-other\\ollama.exe'},
  {ProcessId:702,ExecutablePath:root+'\\..\\system.exe'},
  {ProcessId:703,ExecutablePath:'ollama.exe'},
  {ProcessId:704,ExecutablePath:null},
  {ProcessId:705,ExecutablePath:root+'\\managed\\ollama-0.34.4\\ollama.exe'},
 ];
 assert.deepEqual(ownedWindowsProcesses(root,items),[items[5]].map(x=>({pid:x.ProcessId,executable:x.ExecutablePath})));
});
test('empty, drive-root, relative, malformed or duplicate ownership fails closed',()=>{
 for(const value of ['', 'C:\\', 'relative\\thread-runtime-integration', null]) assert.throws(()=>ownedWindowsProcesses(value,[]));
 assert.throws(()=>ownedWindowsProcesses(root,null));
 const item={ProcessId:1,ExecutablePath:root+'\\runner.exe'};
 assert.throws(()=>ownedWindowsProcesses(root,[item,item]));
 assert.throws(()=>ownedWindowsProcesses(root,[{...item,ProcessId:0}]));
});
test('Windows case normalization still requires a directory boundary',()=>{
 assert.equal(ownedWindowsProcesses(root,[{ProcessId:12,ExecutablePath:root.toUpperCase()+'\\runner.exe'}]).length,1);
});
