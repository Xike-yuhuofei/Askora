const assert = require('node:assert/strict')
const test = require('node:test')

const { createAppMenuTemplate } = require('./app-menu-template.cjs')

test('custom Electron view menu preserves the complete standard zoom controls', () => {
  const noop = () => {}
  const template = createAppMenuTemplate({
    appName: 'Askora',
    navigateToAccount: noop,
    reload: noop,
    forceReload: noop,
    toggleDevTools: noop,
    openExternal: noop,
  })
  const viewMenu = template.find((entry) => entry.label === '视图')

  assert.deepEqual(
    viewMenu.submenu.filter((entry) => entry.role?.toLowerCase().includes('zoom'))
      .map((entry) => entry.role),
    ['resetZoom', 'zoomIn', 'zoomOut'],
  )
})
