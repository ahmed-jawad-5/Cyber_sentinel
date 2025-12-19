const { app, BrowserWindow } = require('electron');
const { spawn } = require('child_process');
const path = require('path');

let receiverProcess;
let senderProcess;

const ROOT = path.join(__dirname, '..');

function startReceiverAPI() {
  receiverProcess = spawn(
    'uvicorn',
    ['api:app', '--host', '127.0.0.1', '--port', '8000'],
    {
      cwd: ROOT,
      env: {
        ...process.env,
        PYTHONPATH: ROOT
      }
    }
  );

  receiverProcess.stdout.on('data', d =>
    console.log('[Receiver]', d.toString())
  );
  receiverProcess.stderr.on('data', d =>
    console.error('[Receiver ERROR]', d.toString())
  );
}

function startSenderAPI() {
  senderProcess = spawn(
    'uvicorn',
    ['client.sender_api:app', '--host', '127.0.0.1', '--port', '8001'],
    {
      cwd: ROOT,
      env: {
        ...process.env,
        PYTHONPATH: ROOT
      }
    }
  );

  senderProcess.stdout.on('data', d =>
    console.log('[Sender]', d.toString())
  );
  senderProcess.stderr.on('data', d =>
    console.error('[Sender ERROR]', d.toString())
  );
}

app.whenReady().then(() => {
  startReceiverAPI();
  startSenderAPI();

  const win = new BrowserWindow({
    width: 1300,
    height: 850,
    webPreferences: {
      contextIsolation: true
    }
  });

  win.loadURL('http://localhost:5173'); // React dev server
});

app.on('will-quit', () => {
  receiverProcess?.kill();
  senderProcess?.kill();
});
