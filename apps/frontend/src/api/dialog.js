import api from './client'
import { getApiBaseURL, getOrCreateDeviceFingerprint } from './client'

// 创建对话会话
export const createSession = (subject, knowledge_point_id, grade_level) =>
  api.post('/dialog/sessions', { subject, knowledge_point_id, grade_level }).then((r) => r.data)

// 获取会话列表
export const getSessions = (page = 1, pageSize = 20) =>
  api.get('/dialog/sessions', {
    params: { limit: pageSize, offset: (page - 1) * pageSize },
  }).then((r) => r.data)

// 获取会话详情
export const getSession = (sessionId) =>
  api.get(`/dialog/sessions/${sessionId}`).then((r) => r.data)

// 获取会话消息
export const getMessages = (sessionId, page = 1, pageSize = 50) =>
  api.get(`/dialog/sessions/${sessionId}/messages`, {
    params: { limit: pageSize, offset: (page - 1) * pageSize },
  }).then((r) => r.data)

// 发送消息
export const sendMessage = (sessionId, content) =>
  api.post(`/dialog/sessions/${sessionId}/messages`, { content }).then((r) => r.data)

// 结束会话
export const endSession = (sessionId) =>
  api.post(`/dialog/sessions/${sessionId}/end`).then((r) => r.data)

/**
 * 解析 SSE 文本流（按 "data: ..." + 空行切分）
 */
function parseSseChunk(buffer) {
  const events = []
  let buf = buffer
  while (true) {
    const idx = buf.indexOf('\n\n')
    if (idx === -1) break
    const raw = buf.slice(0, idx)
    buf = buf.slice(idx + 2)

    const lines = raw.split('\n')
    let event = 'message'
    let data = ''
    for (const line of lines) {
      if (line.startsWith('event:')) event = line.slice(6).trim()
      else if (line.startsWith('data:')) data += line.slice(5).trim()
    }
    if (data) events.push({ event, data })
  }
  return { events, remaining: buf }
}

/**
 * 流式对话（基于 fetch + ReadableStream，通过 POST body 传 content；兼容 GET 模式）。
 *
 * 回调：
 *   onMessage(delta)     收到内容增量或完整片段
 *   onDone(finalPayload) 收到最终状态（含完整 content）
 *   onError(payload)     流式错误/网络错误
 */
export const streamMessage = (sessionId, content, onMessage, onDone, onError) => {
  let closed = false
  let finalReceived = false
  const controller = new AbortController()

  const headers = {
    'Content-Type': 'application/json',
    'X-Device-Fingerprint': getOrCreateDeviceFingerprint(),
  }

  ;(async () => {
    let resp
    try {
      const baseURL = await getApiBaseURL()
      const url = `${baseURL}/dialog/sessions/${encodeURIComponent(sessionId)}/stream`
      resp = await fetch(url, {
        method: 'POST',
        headers,
        credentials: 'include',
        body: JSON.stringify({ content }),
        signal: controller.signal,
      })
    } catch (networkErr) {
      if (!closed && networkErr.name !== 'AbortError' && onError) onError(networkErr)
      return
    }

    // 非 2xx：尝试解析后端统一错误结构，通过事件抛出
    if (!resp.ok) {
      let payload = { code: 'HTTP-' + resp.status, message: '流式请求失败: ' + resp.status }
      try {
        const errJson = await resp.json()
        if (errJson?.error) payload = { ...payload, ...errJson.error }
      } catch {}
      if (!closed && onError) onError(payload)
      return
    }

    if (!resp.body) {
      if (!closed && onError) onError({ message: '浏览器不支持 ReadableStream' })
      return
    }

    const reader = resp.body.getReader()
    const decoder = new TextDecoder('utf-8')
    let buffer = ''
    let finalText = ''

    try {
      while (true) {
        if (controller.signal.aborted) break
        const { done, value } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })

        const { events, remaining } = parseSseChunk(buffer)
        buffer = remaining

        for (const ev of events) {
          let parsed
          try {
            parsed = JSON.parse(ev.data)
          } catch {
            parsed = ev.data
          }

          if (controller.signal.aborted) break
          if (ev.event === 'delta' || ev.event === 'content' || ev.event === 'message') {
            const d = parsed?.delta ?? parsed?.content ?? (typeof parsed === 'string' ? parsed : '')
            if (d) {
              finalText += d
              onMessage?.(d)
            }
          } else if (ev.event === 'final' || ev.event === 'done') {
            finalReceived = true
            if (!closed) onDone?.({ full_text: finalText, ...(parsed || {}) })
          } else if (ev.event === 'violation') {
            if (!closed) onError?.({ violation: true, ...(parsed || {}) })
          } else if (ev.event === 'error') {
            if (!closed) onError?.(parsed || {})
          }
        }
      }

      // 流读完但未触发 final/done：用累计文本兜底回调 onDone
      if (!controller.signal.aborted && !closed && !finalReceived) {
        onDone?.({ full_text: finalText, note: 'final event not received' })
      }
    } catch (err) {
      if (!closed && onError) onError(err)
    } finally {
      try { reader.releaseLock() } catch {}
    }
  })()

  return () => {
    closed = true
    controller.abort()
  }
}
