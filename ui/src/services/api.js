import axios from 'axios'
import { API_BASE_URL } from '../utils/constants'

// Create axios instance with default config
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 60000, // 60 seconds
  headers: {
    'Content-Type': 'application/json',
  }
})

// Request interceptor for logging
apiClient.interceptors.request.use(
  (config) => {
    console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`, config.data)
    return config
  },
  (error) => {
    console.error('API Request Error:', error)
    return Promise.reject(error)
  }
)

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => {
    console.log(`API Response: ${response.status} ${response.config.url}`, response.data)
    return response
  },
  (error) => {
    console.error('API Response Error:', error.response?.data || error.message)
    
    // Transform error for consistent handling
    const apiError = {
      message: error.response?.data?.detail || error.message || 'An unexpected error occurred',
      status: error.response?.status || 0,
      data: error.response?.data || null
    }
    
    return Promise.reject(apiError)
  }
)

/**
 * API Client for ETF GraphRAG services
 */
export const api = {
  /**
   * Main GraphRAG query endpoint with mandatory LLM synthesis
   */
  async askQuery(query) {
    const response = await apiClient.post('/ask/', { query })
    return response.data
  },

  /**
   * Intent classification endpoint for debugging
   */
  async classifyIntent(query) {
    const response = await apiClient.post('/intent/', { query })
    return response.data
  },

  /**
   * Get subgraph data for Cytoscape visualization
   */
  async getSubgraph(ticker, topN = 10, edgeWeightThreshold = 0.0) {
    const response = await apiClient.get('/graph/subgraph', {
      params: {
        ticker,
        top: topN,
        edge_weight_threshold: edgeWeightThreshold
      }
    })
    return response.data
  },

  /**
   * Refresh ETF data with TTL-aware caching
   */
  async refreshETLData(tickers = null, force = false) {
    const response = await apiClient.post('/etl/refresh', {
      tickers,
      force
    })
    return response.data
  },

  /**
   * Force refresh all ETF data ignoring cache
   */
  async forceRefreshETLData() {
    const response = await apiClient.post('/etl/refresh/force')
    return response.data
  },

  /**
   * Get cache statistics
   */
  async getCacheStats() {
    const response = await apiClient.get('/etl/cache/stats')
    return response.data
  },

  /**
   * Health check endpoint
   */
  async healthCheck() {
    const response = await apiClient.get('/health')
    return response.data
  },

  /**
   * Get API information
   */
  async getApiInfo() {
    const response = await apiClient.get('/')
    return response.data
  }
}

/**
 * Hook-friendly API functions with error handling
 */
export const apiHooks = {
  /**
   * Execute query with loading state management
   */
  async executeQuery(query, { onStart, onSuccess, onError, onFinally }) {
    try {
      onStart?.()
      const result = await api.askQuery(query)
      onSuccess?.(result)
      return result
    } catch (error) {
      onError?.(error)
      throw error
    } finally {
      onFinally?.()
    }
  },

  /**
   * Load graph data with loading state management
   */
  async loadGraphData(ticker, topN, threshold, { onStart, onSuccess, onError, onFinally }) {
    try {
      onStart?.()
      const result = await api.getSubgraph(ticker, topN, threshold)
      onSuccess?.(result)
      return result
    } catch (error) {
      onError?.(error)
      throw error
    } finally {
      onFinally?.()
    }
  },

  /**
   * Check API health with timeout
   */
  async checkHealth(timeout = 5000) {
    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), timeout)
    
    try {
      const response = await apiClient.get('/health', {
        signal: controller.signal
      })
      clearTimeout(timeoutId)
      return response.data
    } catch (error) {
      clearTimeout(timeoutId)
      if (error.name === 'AbortError') {
        throw { message: 'Health check timeout', status: 0 }
      }
      throw error
    }
  }
}

export default api