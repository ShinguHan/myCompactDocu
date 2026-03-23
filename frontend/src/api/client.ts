import axios from 'axios'

const client = axios.create({
  baseURL: '/api',
  headers: { 'Content-Type': 'application/json' },
})

client.interceptors.response.use(
  (res) => res,
  (err) => {
    const msg = err.response?.data?.detail || err.message || '오류가 발생했습니다'
    console.error('[API Error]', msg)
    return Promise.reject(new Error(msg))
  }
)

export default client
