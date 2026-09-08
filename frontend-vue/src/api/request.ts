/**
 * Axios 实例封装。
 * - baseURL 为 /api，开发环境由 Vite proxy 代理到 FastAPI（8000）
 * - 响应拦截器统一解包 data 并处理错误提示
 */
import axios, { type AxiosError } from 'axios'
import { ElMessage } from 'element-plus'

const request = axios.create({
  baseURL: '/api',
  timeout: 180000,
})

// 响应拦截：直接返回业务数据；出错统一提示
request.interceptors.response.use(
  (response) => response.data,
  (error: AxiosError<{ detail?: string }>) => {
    const detail =
      error.response?.data?.detail || error.message || '网络请求失败'
    // 404/409 等业务错误交由调用方处理时也提示，但不重复抛出难读信息
    ElMessage.error(typeof detail === 'string' ? detail : '请求失败')
    return Promise.reject(error)
  },
)

export default request
