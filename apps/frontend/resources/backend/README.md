# Electron Backend Resources

> 状态：构建辅助目录说明，不是后端运行文档

`npm run backend:build` 调用 `build-backend.sh`，将 PyInstaller 生成的 FastAPI 后端复制到本目录。`electron-builder` 再通过 `extraResources` 把这些文件嵌入 macOS 应用。

手动执行同一构建脚本：

```bash
bash build-backend.sh
```

这里的二进制和复制文件是生成产物，不应作为源代码、API 合同或当前后端能力的权威来源。
