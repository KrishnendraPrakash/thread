// Runs only against a private CI package in a disposable Windows profile.
const fs = require('node:fs');
const path = require('node:path');
const os = require('node:os');
const crypto = require('node:crypto');
const { spawn, spawnSync } = require('node:child_process');
const { runTests } = require('@vscode/test-electron');

async function main() {
  if (process.platform !== 'win32' || process.arch !== 'x64') throw Error('This installed test requires Windows x64.');
  const extension = path.resolve(__dirname, '..');
  const root = path.resolve(extension, '../..');
  const pin = JSON.parse(fs.readFileSync(path.join(extension, 'test-config/windows-vscode.json'), 'utf8'));
  const manifest = JSON.parse(fs.readFileSync(path.join(extension, 'package.json'), 'utf8'));
  const code = path.resolve(process.env.THREAD_TEST_CODE_EXE || '');
  const vsix = path.resolve(process.env.THREAD_TEST_VSIX || '');
  if (!process.env.THREAD_TEST_CODE_EXE || !process.env.THREAD_TEST_VSIX || !fs.existsSync(code) || !fs.existsSync(vsix)) throw Error('Explicit existing Code executable and private VSIX required.');
  const app = path.join(path.dirname(code), pin.runtime_directory || '', 'resources/app');
  if (JSON.parse(fs.readFileSync(path.join(app, 'package.json'))).version !== pin.version || JSON.parse(fs.readFileSync(path.join(app, 'product.json'))).commit !== pin.commit) throw Error('Pinned Code metadata mismatch.');
  const temporary = fs.mkdtempSync(path.join(os.tmpdir(), 'thread-wincode-'));
  const profile = path.join(temporary, 'profile'), extensions = path.join(temporary, 'extensions'), workspace = path.join(temporary, 'workspace');
  for (const directory of [profile, extensions, workspace]) fs.mkdirSync(directory);
  fs.writeFileSync(path.join(workspace, 'app.py'), 'value = 1\n');
  if (fs.readdirSync(profile).length || fs.readdirSync(extensions).length) throw Error('Profiles must start empty.');
  const cliEnvironment = { ...process.env, ELECTRON_RUN_AS_NODE: '1' };
  const cli = path.join(app, 'out/cli.js');
  const install = spawnSync(code, [cli, '--user-data-dir='+profile, '--extensions-dir='+extensions, '--install-extension', vsix, '--force'], { env: cliEnvironment, encoding: 'utf8', timeout: 120000, shell: false });
  if (install.error || install.status !== 0) throw Error(install.stderr || install.error || 'VSIX installation failed');
  const installed = fs.readdirSync(extensions).map(name => path.join(extensions, name)).find(folder => {
    const file = path.join(folder, 'package.json');
    if (!fs.existsSync(file)) return false;
    const value = JSON.parse(fs.readFileSync(file));
    return value.publisher === manifest.publisher && value.name === manifest.name && value.version === manifest.version;
  });
  if (!installed) throw Error('Expected extension was not installed.');
  const hostEnvironment = { ...process.env }; delete hostEnvironment.ELECTRON_RUN_AS_NODE;
  const expectedLicense = crypto.createHash('sha256').update(fs.readFileSync(path.join(root, 'LICENSE'))).digest('hex');
  // runTests receives the exact installed payload, not source/out as a substitute.
  const options = { vscodeExecutablePath: code, platform: pin.platform,
    extensionDevelopmentPath: installed,
    extensionTestsPath: path.join(extension, process.env.THREAD_TEST_POSITIVE === '1' ? 'out/test/windowsPositiveHost.js' : 'out/test/windowsInstalledHost.js'),
    extensionTestsEnv: { ...hostEnvironment, ELECTRON_RUN_AS_NODE: undefined, THREAD_INSTALLED_VERSION: manifest.version,
      THREAD_INSTALLED_LICENSE_SHA: expectedLicense, THREAD_INSTALLED_PATH: installed,
      THREAD_SOURCE_NOTICE_SHA: crypto.createHash('sha256').update(fs.readFileSync(path.join(extension, 'notices/pathspec-0.12.1-SOURCE.txt'))).digest('hex') },
    launchArgs: [workspace, '--user-data-dir='+profile, '--extensions-dir='+extensions,
      '--disable-extensions', '--disable-telemetry', '--disable-gpu'] };
  if (process.env.THREAD_TEST_POSITIVE !== '1') {
    await runTests(options);
  } else {
    // The pinned SDK host deliberately uses in-memory storage whenever
    // extensionTestsPath is set. A private development driver uses ordinary
    // storage in this same disposable profile; no VS Code binary is patched.
    const driver = path.join(temporary, 'driver'); fs.mkdirSync(driver);
    fs.writeFileSync(path.join(driver, 'package.json'), JSON.stringify({ name: 'thread-private-driver', publisher: 'thread-fixtures',
      version: '0.0.0', engines: { vscode: '^1.95.0' }, main: './runner.cjs', activationEvents: ['onStartupFinished'] }));
    fs.copyFileSync(path.join(extension, 'out/test/windowsPositiveHost.js'), path.join(driver, 'test.js'));
    fs.writeFileSync(path.join(driver, 'runner.cjs'), `const fs = require('node:fs'); const vscode = require('vscode');
exports.activate = async () => {
  try { await require('./test.js').run(); fs.writeFileSync(process.env.THREAD_TEST_REPORT, JSON.stringify({ok:true})); }
  catch (error) { console.error(error); fs.writeFileSync(process.env.THREAD_TEST_REPORT, JSON.stringify({ok:false,error:String(error.stack || error)})); }
  finally { await vscode.commands.executeCommand('workbench.action.quit'); }
};
`);
    for (const phase of ['initial', 'resume']) {
      const report = path.join(temporary, phase+'.json');
      const environment = { ...options.extensionTestsEnv, THREAD_TEST_PHASE: phase, THREAD_TEST_REPORT: report };
      delete environment.ELECTRON_RUN_AS_NODE;
      await new Promise((resolve, reject) => {
        const child = spawn(code, [...options.launchArgs, '--disable-workspace-trust',
          '--extensionDevelopmentPath='+installed, '--extensionDevelopmentPath='+driver], { env: environment, shell: false, stdio: 'inherit' });
        const timer = setTimeout(() => { child.kill(); reject(Error('Private driver timed out: '+phase)); }, 180000);
        child.once('error', error => { clearTimeout(timer); reject(error); });
        child.once('close', status => {
          clearTimeout(timer);
          if (status !== 0 || !fs.existsSync(report)) { reject(Error('Private driver failed without successful completion: '+phase)); return; }
          const result = JSON.parse(fs.readFileSync(report, 'utf8'));
          result.ok ? resolve() : reject(Error(result.error));
        });
      });
      console.log('THREAD_WINDOWS_'+phase.toUpperCase()+'_PHASE_PASSED: installed fixture assertions completed');
    }
    console.log('THREAD_WINDOWS_REAL_PROFILE_RELOAD_PASSED: ordinary isolated storage across two launches; no extensionTestsPath');
  }
  console.log('THREAD_WINDOWS_INSTALLED_PROFILE_PASSED: '+temporary);
}
main().catch(error => { console.error(error); process.exitCode = 1; });
