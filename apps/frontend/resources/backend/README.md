# Backend Resources Directory
# 
# 此目录存放由 build-backend.sh 脚本生成的后端二进制文件。
# 
# 生成方式：
#   npm run backend:build
# 
# 或手动：
#   bash build-backend.sh
# 
# 该脚本会将 PyInstaller 打包后的 FastAPI 后端二进制文件复制到此目录，
# 随后在 electron-builder 打包时通过 extraResources 嵌入到 .app 中。
