import { useState, useMemo } from 'react'
import { ChevronDown, ChevronUp, Download, Table as TableIcon } from 'lucide-react'
import { formatTableCell } from '../../utils/formatters'
import clsx from 'clsx'

function ResultsTable({ rows = [], intent, className = '' }) {
  const [sortConfig, setSortConfig] = useState({ key: null, direction: 'asc' })
  const [currentPage, setCurrentPage] = useState(1)
  const [pageSize, setPageSize] = useState(10)

  // Get column headers from first row, filtering out complex objects
  const columns = useMemo(() => {
    if (!rows.length) return []
    return Object.keys(rows[0]).filter(key => {
      const value = rows[0][key]
      const keyLower = key.toLowerCase()
      
      // Hide complex array/object columns that would show as "[object Object]"
      if (keyLower.includes('holdings') || keyLower.includes('sectors')) {
        return false
      }
      
      // Hide other arrays or objects
      if (Array.isArray(value) || (typeof value === 'object' && value !== null)) {
        return false
      }
      
      return true
    }).map(key => ({
      key,
      header: formatColumnHeader(key),
      sortable: typeof rows[0][key] === 'number' || typeof rows[0][key] === 'string'
    }))
  }, [rows])

  // Sort data
  const sortedRows = useMemo(() => {
    if (!sortConfig.key || !rows.length) return rows

    return [...rows].sort((a, b) => {
      const aVal = a[sortConfig.key]
      const bVal = b[sortConfig.key]

      if (aVal === null || aVal === undefined) return 1
      if (bVal === null || bVal === undefined) return -1

      if (typeof aVal === 'number' && typeof bVal === 'number') {
        return sortConfig.direction === 'asc' ? aVal - bVal : bVal - aVal
      }

      const aStr = String(aVal).toLowerCase()
      const bStr = String(bVal).toLowerCase()
      
      if (sortConfig.direction === 'asc') {
        return aStr.localeCompare(bStr)
      } else {
        return bStr.localeCompare(aStr)
      }
    })
  }, [rows, sortConfig])

  // Paginate data
  const paginatedRows = useMemo(() => {
    const startIndex = (currentPage - 1) * pageSize
    return sortedRows.slice(startIndex, startIndex + pageSize)
  }, [sortedRows, currentPage, pageSize])

  const totalPages = Math.ceil(sortedRows.length / pageSize)

  const handleSort = (key) => {
    setSortConfig(prevConfig => ({
      key,
      direction: prevConfig.key === key && prevConfig.direction === 'asc' ? 'desc' : 'asc'
    }))
  }

  const handleExport = () => {
    if (!rows.length) return

    const csvContent = [
      columns.map(col => col.header).join(','),
      ...sortedRows.map(row =>
        columns.map(col => {
          const value = row[col.key]
          const formattedValue = typeof value === 'string' && value.includes(',') 
            ? `"${value}"` 
            : String(value || '')
          return formattedValue
        }).join(',')
      )
    ].join('\n')

    const blob = new Blob([csvContent], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `etf-analysis-${intent || 'results'}-${new Date().toISOString().split('T')[0]}.csv`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
  }

  if (!rows.length) {
    return (
      <div className={clsx('card', className)}>
        <div className="card-body text-center py-12">
          <TableIcon className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No Data Available</h3>
          <p className="text-gray-500">
            Execute a query to see results in this table.
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className={clsx('card', className)}>
      <div className="card-header">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold text-gray-900">Query Results</h3>
            <p className="text-sm text-gray-500">
              {sortedRows.length} {sortedRows.length === 1 ? 'result' : 'results'}
              {intent && ` • ${formatIntentName(intent)}`}
            </p>
          </div>
          
          <div className="flex items-center space-x-2">
            <select
              value={pageSize}
              onChange={(e) => {
                setPageSize(Number(e.target.value))
                setCurrentPage(1)
              }}
              className="form-select text-sm"
            >
              <option value={10}>10 per page</option>
              <option value={20}>20 per page</option>
              <option value={50}>50 per page</option>
              <option value={100}>100 per page</option>
            </select>
            
            <button
              onClick={handleExport}
              className="btn-outline !p-2"
              title="Export to CSV"
            >
              <Download className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="table">
          <thead className="table-header">
            <tr>
              {columns.map((column) => (
                <th
                  key={column.key}
                  className={clsx(
                    'table-cell-header',
                    column.sortable && 'cursor-pointer hover:bg-gray-100 select-none'
                  )}
                  onClick={() => column.sortable && handleSort(column.key)}
                >
                  <div className="flex items-center space-x-1">
                    <span>{column.header}</span>
                    {column.sortable && (
                      <div className="flex flex-col">
                        <ChevronUp
                          className={clsx(
                            'w-3 h-3 -mb-1',
                            sortConfig.key === column.key && sortConfig.direction === 'asc'
                              ? 'text-primary-600'
                              : 'text-gray-300'
                          )}
                        />
                        <ChevronDown
                          className={clsx(
                            'w-3 h-3',
                            sortConfig.key === column.key && sortConfig.direction === 'desc'
                              ? 'text-primary-600'
                              : 'text-gray-300'
                          )}
                        />
                      </div>
                    )}
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {paginatedRows.map((row, index) => (
              <tr key={index} className="table-row">
                {columns.map((column) => (
                  <td key={column.key} className="table-cell">
                    <span className={getValueClassName(row[column.key], column.key)}>
                      {formatTableCell(row[column.key], column.key)}
                    </span>
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="card-body border-t border-gray-200">
          <div className="flex items-center justify-between">
            <div className="text-sm text-gray-500">
              Showing {((currentPage - 1) * pageSize) + 1} to {Math.min(currentPage * pageSize, sortedRows.length)} of {sortedRows.length} results
            </div>
            
            <div className="flex items-center space-x-2">
              <button
                onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
                disabled={currentPage === 1}
                className="btn-outline !p-2 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <ChevronUp className="w-4 h-4 rotate-90" />
              </button>
              
              <span className="text-sm text-gray-700">
                Page {currentPage} of {totalPages}
              </span>
              
              <button
                onClick={() => setCurrentPage(prev => Math.min(totalPages, prev + 1))}
                disabled={currentPage === totalPages}
                className="btn-outline !p-2 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <ChevronDown className="w-4 h-4 -rotate-90" />
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

function formatColumnHeader(key) {
  return key
    .replace(/_/g, ' ')
    .replace(/\b\w/g, l => l.toUpperCase())
    .replace(/Etf/g, 'ETF')
}

function formatIntentName(intent) {
  return intent
    .replace(/_/g, ' ')
    .replace(/\b\w/g, l => l.toUpperCase())
}

function getValueClassName(value, key) {
  const keyLower = key.toLowerCase()
  
  if (typeof value === 'number') {
    if (keyLower.includes('weight') || keyLower.includes('exposure') || keyLower.includes('percent')) {
      if (value >= 0.1) return 'font-medium text-green-700'
      if (value >= 0.05) return 'font-medium text-yellow-700'
      if (value > 0) return 'font-medium text-gray-600'
    }
    
    if (keyLower.includes('confidence') || keyLower.includes('similarity')) {
      if (value >= 0.8) return 'font-medium text-green-700'
      if (value >= 0.6) return 'font-medium text-yellow-700'
      if (value > 0) return 'font-medium text-red-600'
    }
  }
  
  return 'text-gray-900'
}

export default ResultsTable