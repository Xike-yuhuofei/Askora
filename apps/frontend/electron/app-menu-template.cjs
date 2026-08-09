function createAppMenuTemplate({
  appName,
  navigateToAccount,
  reload,
  forceReload,
  toggleDevTools,
  openExternal,
}) {
  return [
    {
      label: appName,
      submenu: [
        { role: 'about' },
        { type: 'separator' },
        {
          label: '设置',
          accelerator: 'CmdOrCtrl+,',
          click: navigateToAccount,
        },
        { type: 'separator' },
        { role: 'services' },
        { type: 'separator' },
        { role: 'hide' },
        { role: 'hideOthers' },
        { role: 'unhide' },
        { type: 'separator' },
        { role: 'quit' },
      ],
    },
    {
      label: '编辑',
      submenu: [
        { role: 'undo' },
        { role: 'redo' },
        { type: 'separator' },
        { role: 'cut' },
        { role: 'copy' },
        { role: 'paste' },
        { role: 'selectAll' },
      ],
    },
    {
      label: '视图',
      submenu: [
        { label: '刷新', accelerator: 'CmdOrCtrl+R', click: reload },
        { label: '强制刷新', accelerator: 'CmdOrCtrl+Shift+R', click: forceReload },
        { type: 'separator' },
        { role: 'resetZoom' },
        { role: 'zoomIn' },
        { role: 'zoomOut' },
        { type: 'separator' },
        { role: 'togglefullscreen' },
        { label: '开发者工具', accelerator: 'F12', click: toggleDevTools },
      ],
    },
    {
      label: '窗口',
      submenu: [
        { role: 'minimize' },
        { role: 'zoom' },
        { type: 'separator' },
        { role: 'bringAllToFront' },
      ],
    },
    {
      label: '帮助',
      submenu: [
        { label: 'Askora 文档', click: () => openExternal('https://docs.askora.com') },
        { label: '反馈问题', click: () => openExternal('https://github.com/askora/feedback') },
      ],
    },
  ]
}

module.exports = { createAppMenuTemplate }
