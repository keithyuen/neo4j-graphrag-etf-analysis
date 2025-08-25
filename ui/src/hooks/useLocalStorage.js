import { useState, useEffect, useCallback } from 'react'

/**
 * Hook for managing localStorage with JSON serialization
 */
export function useLocalStorage(key, defaultValue) {
  const [value, setValue] = useState(() => {
    try {
      const item = window.localStorage.getItem(key)
      return item ? JSON.parse(item) : defaultValue
    } catch (error) {
      console.warn(`Error reading localStorage key "${key}":`, error)
      return defaultValue
    }
  })

  const setStoredValue = useCallback((value) => {
    try {
      setValue(value)
      window.localStorage.setItem(key, JSON.stringify(value))
    } catch (error) {
      console.warn(`Error setting localStorage key "${key}":`, error)
    }
  }, [key])

  const removeStoredValue = useCallback(() => {
    try {
      setValue(defaultValue)
      window.localStorage.removeItem(key)
    } catch (error) {
      console.warn(`Error removing localStorage key "${key}":`, error)
    }
  }, [key, defaultValue])

  return [value, setStoredValue, removeStoredValue]
}

/**
 * Hook for managing user preferences
 */
export function useUserPreferences() {
  const [preferences, setPreferences] = useLocalStorage('etf-graphrag-preferences', {
    theme: 'light',
    graphLayout: 'cose-bilkent',
    defaultTopN: 10,
    defaultEdgeThreshold: 0.0,
    autoRefreshData: false,
    showDiagnostics: true,
    animationsEnabled: true
  })

  const updatePreference = useCallback((key, value) => {
    setPreferences(prev => ({
      ...prev,
      [key]: value
    }))
  }, [setPreferences])

  const resetPreferences = useCallback(() => {
    setPreferences({
      theme: 'light',
      graphLayout: 'cose-bilkent',
      defaultTopN: 10,
      defaultEdgeThreshold: 0.0,
      autoRefreshData: false,
      showDiagnostics: true,
      animationsEnabled: true
    })
  }, [setPreferences])

  return {
    preferences,
    updatePreference,
    resetPreferences
  }
}

/**
 * Hook for managing query history
 */
export function useQueryHistory() {
  const [history, setHistory] = useLocalStorage('etf-graphrag-query-history', [])

  const addQuery = useCallback((query, result) => {
    const newEntry = {
      id: Date.now(),
      query,
      result: {
        intent: result.intent,
        answer: result.answer,
        rowCount: result.rows?.length || 0,
        confidence: result.metadata?.confidence || 0
      },
      timestamp: new Date().toISOString()
    }

    setHistory(prev => [newEntry, ...prev.slice(0, 49)]) // Keep last 50 queries
  }, [setHistory])

  const removeQuery = useCallback((id) => {
    setHistory(prev => prev.filter(entry => entry.id !== id))
  }, [setHistory])

  const clearHistory = useCallback(() => {
    setHistory([])
  }, [setHistory])

  const searchHistory = useCallback((searchTerm) => {
    if (!searchTerm) return history
    
    const term = searchTerm.toLowerCase()
    return history.filter(entry => 
      entry.query.toLowerCase().includes(term) ||
      entry.result.intent.toLowerCase().includes(term) ||
      entry.result.answer.toLowerCase().includes(term)
    )
  }, [history])

  return {
    history,
    addQuery,
    removeQuery,
    clearHistory,
    searchHistory
  }
}

/**
 * Hook for managing graph settings cache
 */
export function useGraphSettings() {
  const [settings, setSettings] = useLocalStorage('etf-graphrag-graph-settings', {
    lastTicker: 'SPY',
    lastTopN: 10,
    lastEdgeThreshold: 0.0,
    lastLayout: 'cose-bilkent',
    savedLayouts: {
      'cose-bilkent': { name: 'cose-bilkent' },
      'fcose': { name: 'fcose' },
      'cola': { name: 'cola' }
    }
  })

  const updateSetting = useCallback((key, value) => {
    setSettings(prev => ({
      ...prev,
      [key]: value
    }))
  }, [setSettings])

  const saveLayoutSettings = useCallback((layoutName, layoutOptions) => {
    setSettings(prev => ({
      ...prev,
      savedLayouts: {
        ...prev.savedLayouts,
        [layoutName]: layoutOptions
      }
    }))
  }, [setSettings])

  const getLayoutSettings = useCallback((layoutName) => {
    return settings.savedLayouts?.[layoutName] || { name: layoutName }
  }, [settings])

  return {
    settings,
    updateSetting,
    saveLayoutSettings,
    getLayoutSettings
  }
}