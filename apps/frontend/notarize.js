#!/usr/bin/env node
/**
 * Askora macOS Notarization Script
 * 
 * 使用前请先安装 @electron/notarize（已列入 devDependencies）。
 * 
 * 并设置以下环境变量：
 *   APPLE_ID          - Apple Developer 账号
 *   APPLE_APP_SPECIFIC_PASSWORD - App-specific password
 *   APPLE_TEAM_ID     - Team ID
 * 
 * 使用方法：
 *   npm run notarize
 */

const path = require('path')

async function notarize() {
  try {
    const { notarize } = require('@electron/notarize')
    const fs = require('fs')

    const { APPLE_ID, APPLE_APP_SPECIFIC_PASSWORD, APPLE_TEAM_ID } = process.env

    if (!APPLE_ID || !APPLE_APP_SPECIFIC_PASSWORD || !APPLE_TEAM_ID) {
      console.error('[Notarize] 缺少 Apple 凭据环境变量')
      console.error('请设置：APPLE_ID, APPLE_APP_SPECIFIC_PASSWORD, APPLE_TEAM_ID')
      process.exit(1)
    }

    const candidates = [
      path.join(__dirname, 'release', 'mac-arm64', 'Askora.app'),
      path.join(__dirname, 'release', 'mac', 'Askora.app'),
      path.join(__dirname, 'release', 'mac-universal', 'Askora.app'),
    ]
    const appPath = candidates.find((candidate) => fs.existsSync(candidate))
    
    if (!appPath) {
      console.error(`[Notarize] 找不到 .app 文件，已检查: ${candidates.join(', ')}`)
      console.error('请先运行 npm run electron:build:mac')
      process.exit(1)
    }

    console.log(`[Notarize] 正在提交 ${appPath} 进行 Apple 公证...`)

    await notarize({
      appPath,
      appleId: APPLE_ID,
      appleIdPassword: APPLE_APP_SPECIFIC_PASSWORD,
      teamId: APPLE_TEAM_ID,
      tool: 'notarytool',
    })

    console.log('[Notarize] ✅ 公证成功！')
  } catch (error) {
    console.error('[Notarize] ❌ 公证失败：', error.message)
    process.exit(1)
  }
}

notarize()
