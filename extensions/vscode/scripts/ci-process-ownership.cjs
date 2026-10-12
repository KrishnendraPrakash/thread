// Pure ownership classification. A process query never authorizes termination.
const path = require('node:path');
function ownedWindowsProcesses(root, records) {
  if (typeof root !== 'string' || !path.win32.isAbsolute(root)
      || path.win32.basename(path.win32.normalize(root)).toLowerCase() !== 'thread-runtime-integration') {
    throw Error('Require the dedicated absolute owned integration directory.');
  }
  const prefix = path.win32.normalize(root).replace(/[\\/]+$/, '')+'\\';
  if (!Array.isArray(records)) throw Error('Process inventory must be an explicit array.');
  const result=[], seen=new Set();
  for (const item of records) {
    if (!item || typeof item.ExecutablePath !== 'string' || !path.win32.isAbsolute(item.ExecutablePath)) continue;
    const executable=path.win32.normalize(item.ExecutablePath);
    if (!executable.toLowerCase().startsWith(prefix.toLowerCase())) continue;
    if (!Number.isInteger(item.ProcessId) || item.ProcessId <= 0 || item.ProcessId > 0xffffffff || seen.has(item.ProcessId)) {
      throw Error('Ambiguous owned process identity.');
    }
    seen.add(item.ProcessId); result.push({pid:item.ProcessId,executable});
  }
  return result;
}
module.exports={ownedWindowsProcesses};
