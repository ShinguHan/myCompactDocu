import axios from 'axios'

const client = axios.create({
  baseURL: '/api',
  headers: { 'Content-Type': 'application/json' },
})

client.interceptors.response.use(
  (res) => res,
  (err) => {
    const detail = err.response?.data?.detail
    const msg = Array.isArray(detail)
      ? detail.map((d: any) => `${d.loc?.slice(1).join('.')}: ${d.msg}`).join(', ')
      : detail || err.message || '오류가 발생했습니다'
    console.error('[API Error]', err.response?.status, msg)
    return Promise.reject(new Error(msg))
  }
)

export default client
