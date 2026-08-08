import api from './client'

export const getTodayWorkspace = (timezone = Intl.DateTimeFormat().resolvedOptions().timeZone) =>
  api.get('/workspace/today', { params: { timezone: timezone || 'Asia/Shanghai' } })
    .then((response) => response.data)
