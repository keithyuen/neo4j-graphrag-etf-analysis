import { useState, useCallback } from 'react'
import { apiHooks } from '../services/api'

/**
 * Hook for managing GraphRAG query state and execution
 */
export function useQuery() {
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)
  const [history, setHistory] = useState([])

  const executeQuery = useCallback(async (query) => {
    if (!query?.trim()) {
      setError({ message: 'Query cannot be empty' })
      return
    }

    setError(null)
    
    try {
      const result = await apiHooks.executeQuery(query, {
        onStart: () => setLoading(true),
        onSuccess: (data) => {
          setResult(data)
          setHistory(prev => [
            { query, result: data, timestamp: new Date().toISOString() },
            ...prev.slice(0, 9) // Keep last 10 queries
          ])
        },
        onError: (err) => setError(err),
        onFinally: () => setLoading(false)
      })
      
      return result
    } catch (err) {
      // Error already set in onError callback
      return null
    }
  }, [])

  const clearResult = useCallback(() => {
    setResult(null)
    setError(null)
  }, [])

  const clearHistory = useCallback(() => {
    setHistory([])
  }, [])

  const retryLastQuery = useCallback(() => {
    const lastQuery = history[0]
    if (lastQuery) {
      return executeQuery(lastQuery.query)
    }
  }, [history, executeQuery])

  return {
    loading,
    result,
    error,
    history,
    executeQuery,
    clearResult,
    clearHistory,
    retryLastQuery
  }
}

/**
 * Hook for managing intent classification
 */
export function useIntentClassification() {
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)

  const classifyIntent = useCallback(async (query) => {
    if (!query?.trim()) {
      setError({ message: 'Query cannot be empty' })
      return
    }

    setLoading(true)
    setError(null)
    
    try {
      const { classifyIntent } = await import('../services/api')
      const result = await classifyIntent(query)
      setResult(result)
      return result
    } catch (err) {
      setError(err)
      return null
    } finally {
      setLoading(false)
    }
  }, [])

  const clearResult = useCallback(() => {
    setResult(null)
    setError(null)
  }, [])

  return {
    loading,
    result,
    error,
    classifyIntent,
    clearResult
  }
}