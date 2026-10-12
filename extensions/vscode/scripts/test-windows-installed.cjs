// Runs only against a private CI package in a disposable Windows profile.
const fs = require('node:fs');
const path = require('node:path');
const os = require('node:os');
const crypto = require('node:crypto');
const { spawnSync } = require('node:child_process');
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
  await runTests({ vscodeExecutablePath: code, platform: pin.platform,
    extensionDevelopmentPath: installed,
    extensionTestsPath: path.join(extension, 'out/test/windowsInstalledHost.js'),
    extensionTestsEnv: { ...hostEnvironment, ELECTRON_RUN_AS_NODE: undefined, THREAD_INSTALLED_VERSION: manifest.version,
      THREAD_INSTALLED_LICENSE_SHA: expectedLicense, THREAD_INSTALLED_PATH: installed },
    launchArgs: [workspace, '--user-data-dir='+profile, '--extensions-dir='+extensions,
      '--disable-extensions', '--disable-telemetry', '--disable-gpu'] });
  console.log('THREAD_WINDOWS_INSTALLED_PROFILE_PASSED: '+temporary);
}
main().catch(error => { console.error(error); process.exitCode = 1; });
