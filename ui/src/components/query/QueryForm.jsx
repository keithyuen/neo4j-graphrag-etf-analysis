import { useState } from 'react'
import { Send, Sparkles, Clock } from 'lucide-react'
import LoadingSpinner from '../common/LoadingSpinner'
import { EXAMPLE_QUERIES, UI_SETTINGS } from '../../utils/constants'

function QueryForm({ onSubmit, loading = false, className = '' }) {
  const [query, setQuery] = useState('')
  const [selectedExample, setSelectedExample] = useState('')

  const handleSubmit = (e) => {
    e.preventDefault()
    if (query.trim() && !loading) {
      onSubmit(query.trim())
    }
  }

  const handleExampleClick = (exampleQuery) => {
    setQuery(exampleQuery)
    setSelectedExample(exampleQuery)
  }

  const handleInputChange = (e) => {
    const value = e.target.value
    if (value.length <= UI_SETTINGS.maxQueryLength) {
      setQuery(value)
      setSelectedExample('')
    }
  }

  const isSubmitDisabled = !query.trim() || loading

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Main Query Form */}
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label htmlFor="query" className="form-label">
            Ask about ETF holdings, overlaps, and exposures
          </label>
          <div className="relative">
            <textarea
              id="query"
              name="query"
              value={query}
              onChange={handleInputChange}
              placeholder="e.g., What is SPY's exposure to AAPL?"
              className="form-textarea h-24 pr-12 resize-none"
              disabled={loading}
              rows={3}
            />
            <div className="absolute bottom-2 right-2 flex items-center space-x-2">
              <span className="text-xs text-gray-400">
                {query.length}/{UI_SETTINGS.maxQueryLength}
              </span>
              {loading && <LoadingSpinner size="sm" />}
            </div>
          </div>
        </div>

        <button
          type="submit"
          disabled={isSubmitDisabled}
          className="btn-primary w-full flex items-center justify-center space-x-2 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? (
            <>
              <LoadingSpinner size="sm" color="white" />
              <span>Processing...</span>
            </>
          ) : (
            <>
              <Send className="w-4 h-4" />
              <span>Ask Question</span>
            </>
          )}
        </button>
      </form>

      {/* Example Queries */}
      <div className="space-y-3">
        <div className="flex items-center space-x-2">
          <Sparkles className="w-4 h-4 text-primary-500" />
          <h3 className="text-sm font-medium text-gray-700">Example Queries</h3>
        </div>
        
        <div className="grid gap-2">
          {EXAMPLE_QUERIES.map((example, index) => (
            <button
              key={index}
              type="button"
              onClick={() => handleExampleClick(example.text)}
              disabled={loading}
              className={`text-left p-3 rounded-lg border transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed ${
                selectedExample === example.text
                  ? 'border-primary-300 bg-primary-50 text-primary-700'
                  : 'border-gray-200 bg-white hover:border-gray-300 hover:bg-gray-50'
              }`}
            >
              <div className="text-sm font-medium text-gray-900">
                {example.text}
              </div>
              <div className="text-xs text-gray-500 mt-1">
                {example.description}
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Quick Tips */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <div className="flex items-start space-x-2">
          <Clock className="w-4 h-4 text-blue-600 mt-0.5 flex-shrink-0" />
          <div className="text-sm text-blue-800">
            <div className="font-medium mb-1">Tips for better results:</div>
            <ul className="space-y-1 text-xs">
              <li>• Use specific ETF tickers: SPY, QQQ, IWM, IJH, IVE, IVW</li>
              <li>• Include company symbols: AAPL, MSFT, GOOGL, etc.</li>
              <li>• Specify percentages: "at least 5%", "more than 10%"</li>
              <li>• Ask for specific numbers: "top 15 holdings"</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  )
}

export default QueryForm