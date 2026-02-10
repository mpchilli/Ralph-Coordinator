const { app, BrowserWindow } = require('electron');
const path = require('path');

function createWindow() {
    const win = new BrowserWindow({
        width: 1280,
        height: 800,
        title: 'Ralph Orchestrator',
        webPreferences: {
            nodeIntegration: false,
            contextIsolation: true,
        },
    });

    // In development, load from the Vite dev server
    // In production, we would load the built files
    win.loadURL('http://localhost:5173');

    // Open DevTools if needed
    // win.webContents.openDevTools();
}

app.whenReady().then(() => {
    createWindow();

    app.on('activate', () => {
        if (BrowserWindow.getAllWindows().length === 0) {
            createWindow();
        }
    });
});

app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') {
        app.quit();
    }
});
