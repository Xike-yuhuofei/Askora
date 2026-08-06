import api from './client'
import axios from 'axios'
import { getApiBaseURL } from './client'

// 获取用户画像
export const getProfile = () => api.get('/users/profile').then((r) => r.data)

// 获取私人运行模式和 LLM 是否配置；接口不返回任何密钥或连接信息。
export const getSystemConfig = async () => {
  const apiBase = await getApiBaseURL()
  const backendOrigin = apiBase.replace(/\/api\/v1\/?$/, '')
  return axios.get(`${backendOrigin}/health/config`, { timeout: 5000 }).then((r) => r.data)
}
