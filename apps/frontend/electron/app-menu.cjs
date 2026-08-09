const { Menu, shell, app } = require('electron')
const { createAppMenuTemplate } = require('./app-menu-template.cjs')

function createAppMenu(mainWindow) {
  return Menu.buildFromTemplate(createAppMenuTemplate({
    appName: app.name,
    navigateToAccount: () => mainWindow.webContents.send('navigate', '/account'),
    reload: () => mainWindow.reload(),
    forceReload: () => mainWindow.webContents.reloadIgnoringCache(),
    toggleDevTools: () => mainWindow.webContents.toggleDevTools(),
    openExternal: (url) => shell.openExternal(url),
  }))
}

module.exports = { createAppMenu }
