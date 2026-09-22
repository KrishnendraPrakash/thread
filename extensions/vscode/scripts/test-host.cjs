// Uses the user's installed VS Code, with an isolated workspace and profile.
const { spawn } = require('node:child_process');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const root = path.resolve(__dirname, '..');
const temporary = fs.mkdtempSync(path.join(os.tmpdir(), 'thread-host-'));
fs.mkdirSync(path.join(temporary, 'workspace'));
fs.writeFileSync(path.join(temporary, 'workspace', 'app.py'), 'value = 1\n');
const executable = process.env.VSCODE_EXECUTABLE || '/Applications/Visual Studio Code.app/Contents/MacOS/Code';
const env = { ...process.env, THREAD_TEST_ROOT: temporary };
delete env.ELECTRON_RUN_AS_NODE;
const child = spawn(executable, [path.join(temporary, 'workspace'), '--new-window', '--skip-welcome', '--skip-release-notes',
  '--disable-workspace-trust', '--disable-extensions', '--disable-telemetry', '--user-data-dir=' + path.join(temporary, 'profile'),
  '--extensions-dir=' + path.join(temporary, 'extensions'), '--extensionDevelopmentPath=' + root,
  '--extensionTestsPath=' + path.join(root, 'out/test/host.js')], { env, stdio: 'inherit' });
const timeout = setTimeout(() => { child.kill('SIGTERM'); }, 90000);
child.on('error', error => { console.error(error); clearTimeout(timeout); process.exitCode = 1; });
child.on('exit', code => { clearTimeout(timeout); console.log('Isolated VS Code fixture: ' + temporary); process.exitCode = code ?? 1; });
