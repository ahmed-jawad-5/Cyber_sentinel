const { app, BrowserWindow } = require('electron');
const path = require('path');
const { spawn } = require('child_process');

let mainWindow;
let pythonProcess;

// project root = one level above gui-react
const PROJECT_ROOT = path.resolve(__dirname, '..');

function startPythonBackend() {
    pythonProcess = spawn(
        'python',
        ['server/api.py'],
        {
            cwd: PROJECT_ROOT,
            env: {
                ...process.env,
                PYTHONPATH: PROJECT_ROOT
            }
        }
    );

    pythonProcess.stdout.on('data', (data) => {
        console.log(`[Python]: ${data}`);
    });

    pythonProcess.stderr.on('data', (data) => {
        console.error(`[Python ERROR]: ${data}`);
    });

    pythonProcess.on('close', (code) => {
        console.log(`Python exited with code ${code}`);
    });
}

function createWindow() {
    mainWindow = new BrowserWindow({
        width: 1400,
        height: 900,
        webPreferences: {
            nodeIntegration: false,
            contextIsolation: true
        }
    });

    mainWindow.loadFile(
        path.join(__dirname, 'dist', 'index.html')
    );

    mainWindow.on('closed', () => {
        if (pythonProcess) pythonProcess.kill('SIGTERM');
        mainWindow = null;
    });
}

app.whenReady().then(() => {
    startPythonBackend();
    createWindow();
});

app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') app.quit();
});

app.on('activate', () => {
    if (mainWindow === null) createWindow();
});
