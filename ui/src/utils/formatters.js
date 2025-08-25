/**
 * Utility functions for formatting data display
 */

/**
 * Format a number as a percentage
 */
export function formatPercentage(value, decimals = 1) {
  if (value === null || value === undefined || isNaN(value)) {
    return 'N/A'
  }
  return `${(value * 100).toFixed(decimals)}%`
}

/**
 * Format a number with proper decimal places
 */
export function formatNumber(value, decimals = 1) {
  if (value === null || value === undefined || isNaN(value)) {
    return 'N/A'
  }
  return Number(value).toFixed(decimals)
}

/**
 * Format large numbers with K/M/B suffixes
 */
export function formatLargeNumber(value, decimals = 1) {
  if (value === null || value === undefined || isNaN(value)) {
    return 'N/A'
  }
  
  const num = Math.abs(value)
  
  if (num >= 1e9) {
    return (value / 1e9).toFixed(decimals) + 'B'
  } else if (num >= 1e6) {
    return (value / 1e6).toFixed(decimals) + 'M'
  } else if (num >= 1e3) {
    return (value / 1e3).toFixed(decimals) + 'K'
  } else {
    return value.toFixed(decimals)
  }
}

/**
 * Format currency values
 */
export function formatCurrency(value, currency = 'USD', decimals = 2) {
  if (value === null || value === undefined || isNaN(value)) {
    return 'N/A'
  }
  
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: currency,
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals
  }).format(value)
}

/**
 * Format execution time in milliseconds
 */
export function formatExecutionTime(ms) {
  if (ms === null || ms === undefined || isNaN(ms)) {
    return 'N/A'
  }
  
  if (ms < 1000) {
    return `${Math.round(ms)}ms`
  } else {
    return `${(ms / 1000).toFixed(2)}s`
  }
}

/**
 * Format confidence scores
 */
export function formatConfidence(confidence) {
  if (confidence === null || confidence === undefined || isNaN(confidence)) {
    return 'N/A'
  }
  return `${Math.round(confidence * 100)}%`
}

/**
 * Format table cell values based on type
 */
export function formatTableCell(value, key) {
  if (value === null || value === undefined) {
    return 'N/A'
  }
  
  const keyLower = key.toLowerCase()
  
  // Handle complex objects and arrays - hide them from table display
  if (keyLower.includes('holdings') || keyLower.includes('sectors')) {
    if (Array.isArray(value)) {
      return `${value.length} items`
    } else if (typeof value === 'object' && value !== null) {
      return '[Complex Object]'
    }
  }
  
  // Handle any other arrays or objects generically
  if (Array.isArray(value)) {
    if (value.length === 0) {
      return 'Empty'
    }
    // For small arrays, show the values
    if (value.length <= 3 && value.every(v => typeof v === 'string' || typeof v === 'number')) {
      return value.join(', ')
    }
    return `${value.length} items`
  }
  
  // Handle generic objects
  if (typeof value === 'object' && value !== null) {
    return '[Object]'
  }
  
  // Percentage values (check this first to avoid double conversion)
  if (keyLower.includes('percent') || keyLower.includes('ratio')) {
    if (typeof value === 'number') {
      return `${value.toFixed(1)}%`
    }
  }
  
  // Weight and exposure values (but not percentages)
  if (keyLower.includes('weight') || keyLower.includes('exposure')) {
    if (typeof value === 'number') {
      return formatPercentage(value, 1)
    }
  }
  
  // Count values
  if (keyLower.includes('count') || keyLower === 'intersection') {
    if (typeof value === 'number') {
      return Math.round(value).toLocaleString()
    }
  }
  
  // Large number values (shares)
  if (keyLower.includes('shares')) {
    if (typeof value === 'number') {
      return formatLargeNumber(value, 0)
    }
  }
  
  // Similarity and overlap values
  if (keyLower.includes('similarity') || keyLower.includes('jaccard')) {
    if (typeof value === 'number') {
      return formatNumber(value, 1)
    }
  }
  
  // Default formatting for numbers
  if (typeof value === 'number') {
    return formatNumber(value, 1)
  }
  
  // String values
  return String(value)
}

/**
 * Format entity names for display
 */
export function formatEntityName(entity) {
  if (!entity) return 'Unknown'
  
  if (entity.type === 'Percent') {
    return formatPercentage(entity.properties?.value || 0)
  }
  
  if (entity.type === 'Count') {
    return entity.properties?.value?.toString() || entity.name
  }
  
  return entity.name
}

/**
 * Format timing data for display
 */
export function formatTimingData(timing) {
  if (!timing || typeof timing !== 'object') {
    return {}
  }
  
  const formatted = {}
  
  for (const [key, value] of Object.entries(timing)) {
    formatted[key] = formatExecutionTime(value)
  }
  
  return formatted
}

/**
 * Truncate text with ellipsis
 */
export function truncateText(text, maxLength = 50) {
  if (!text || text.length <= maxLength) {
    return text
  }
  
  return text.substring(0, maxLength - 3) + '...'
}

/**
 * Format node labels for graph display
 */
export function formatNodeLabel(node) {
  if (!node) return ''
  
  const label = node.label || node.id || ''
  
  // Truncate long labels for better graph display
  if (node.type === 'Sector') {
    return truncateText(label, 15)
  } else if (node.type === 'Company') {
    return truncateText(label, 10)
  } else {
    return truncateText(label, 8)
  }
}

/**
 * Format edge weights for display
 */
export function formatEdgeWeight(weight) {
  if (weight === null || weight === undefined || isNaN(weight)) {
    return '0%'
  }
  
  return formatPercentage(weight, 1)
}