import { useState } from 'react'
import QueryForm from '../components/query/QueryForm'
import LLMAnswer from '../components/query/LLMAnswer'
import ResultsTable from '../components/query/ResultsTable'
import RouterDiagnostics from '../components/query/RouterDiagnostics'
import { useQuery } from '../hooks/useQuery'
import { useUserPreferences } from '../hooks/useLocalStorage'
import { api } from '../services/api'

function Home() {
  const { loading, result, error, executeQuery, clearResult } = useQuery()
  const { preferences } = useUserPreferences()
  const [showDiagnostics, setShowDiagnostics] = useState(preferences.showDiagnostics)
  const [etlLoading, setEtlLoading] = useState(false)
  const [etlResult, setEtlResult] = useState(null)
  const [etlError, setEtlError] = useState(null)

  const handleQuerySubmit = async (query) => {
    await executeQuery(query)
  }

  const handleClearResults = () => {
    clearResult()
  }

  const handleETLRefresh = async () => {
    setEtlLoading(true)
    setEtlError(null)
    setEtlResult(null)

    try {
      console.log('Starting ETL refresh...')
      const result = await api.forceRefreshETLData()
      console.log('ETL refresh completed:', result)
      setEtlResult(result)
    } catch (error) {
      console.error('ETL refresh failed:', error)
      setEtlError(error)
    } finally {
      setEtlLoading(false)
    }
  }

  const clearETLResults = () => {
    setEtlResult(null)
    setEtlError(null)
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header Section */}
      <div className="text-center mb-8">
        <h1 className="text-4xl font-bold text-gray-900 mb-4">
          ETF Analysis with GraphRAG
        </h1>
        <p className="text-xl text-gray-600 max-w-3xl mx-auto">
          Ask natural language questions about ETF holdings, overlaps, and sector exposures. 
          Powered by Neo4j GraphRAG with LLM answer synthesis.
        </p>
      </div>

      {/* Main Content */}
      <div className="space-y-8">
        {/* Error Display */}
        {error && (
          <div className="alert alert-error animate-fade-in">
            <div className="font-medium">Query Error</div>
            <div className="text-sm mt-1">{error.message}</div>
            <button 
              onClick={handleClearResults}
              className="btn-outline mt-3 text-sm"
            >
              Clear and Try Again
            </button>
          </div>
        )}

        {/* Results Section - Moved above query form */}
        {result && !error && (
          <div className="space-y-6 animate-fade-in">
            {/* LLM Answer - Prominently displayed */}
            <LLMAnswer 
              answer={result.answer} 
              metadata={result.metadata}
            />

            {/* Results Table */}
            {result.rows && result.rows.length > 0 && (
              <ResultsTable 
                rows={result.rows}
                intent={result.intent}
              />
            )}

            {/* Router Diagnostics - Collapsible */}
            <div className="flex items-center justify-between mb-4">
              <div></div>
              <label className="flex items-center space-x-2 text-sm text-gray-600">
                <input
                  type="checkbox"
                  checked={showDiagnostics}
                  onChange={(e) => setShowDiagnostics(e.target.checked)}
                  className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                />
                <span>Show pipeline diagnostics</span>
              </label>
            </div>

            {showDiagnostics && (
              <RouterDiagnostics
                intent={result.intent}
                entities={result.entities}
                metadata={result.metadata}
                cypher={result.cypher}
              />
            )}

            {/* Action Buttons */}
            <div className="flex items-center justify-center space-x-4 pt-6">
              <button 
                onClick={handleClearResults}
                className="btn-secondary"
              >
                Clear Results
              </button>
              
              <button 
                onClick={() => window.open('/graph', '_blank')}
                className="btn-primary"
                disabled={!result.intent || result.intent !== 'top_holdings_subgraph'}
              >
                View in Graph
              </button>
            </div>
          </div>
        )}

        {/* Query Form - Moved below results */}
        <QueryForm 
          onSubmit={handleQuerySubmit}
          loading={loading}
        />

        {/* Getting Started Section */}
        {!result && !loading && !error && (
          <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-lg p-8 animate-fade-in">
            <div className="max-w-4xl mx-auto">
              <h2 className="text-2xl font-bold text-gray-900 mb-6 text-center">
                Getting Started
              </h2>

              {/* ETL Data Management Section */}
              <div className="mb-8 p-4 bg-white/80 border border-blue-200 rounded">
                <div className="flex items-center justify-between mb-4">
                  <h4 className="font-medium text-gray-900">ETF Data Management</h4>
                  <button 
                    onClick={handleETLRefresh}
                    disabled={etlLoading}
                    className={`px-4 py-2 rounded text-sm font-medium transition-colors ${
                      etlLoading 
                        ? 'bg-gray-100 text-gray-400 cursor-not-allowed' 
                        : 'bg-blue-600 text-white hover:bg-blue-700'
                    }`}
                  >
                    {etlLoading ? 'Refreshing Data...' : 'Refresh ETF Data'}
                  </button>
                </div>
                
                <p className="text-sm text-gray-700 mb-4">
                  Load the latest ETF holdings data from official sources (SPY, QQQ, IWM, IJH, IVE, IVW). 
                  This downloads real holdings data and may take a few minutes.
                </p>

                {/* ETL Status Display */}
                {etlResult && (
                  <div className="mt-4 p-3 bg-green-50 border border-green-200 rounded animate-fade-in">
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="font-medium text-green-800">Data Refresh Completed</div>
                        <div className="text-sm text-green-700 mt-1">{etlResult.message}</div>
                        {etlResult.tickers_processed && etlResult.tickers_processed.length > 0 && (
                          <div className="text-sm text-green-600 mt-1">
                            Processed ETFs: {etlResult.tickers_processed.join(', ')}
                          </div>
                        )}
                      </div>
                      <button 
                        onClick={clearETLResults}
                        className="text-sm text-green-600 hover:text-green-800"
                      >
                        ✕
                      </button>
                    </div>
                  </div>
                )}

                {etlError && (
                  <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded animate-fade-in">
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="font-medium text-red-800">Data Refresh Failed</div>
                        <div className="text-sm text-red-700 mt-1">{etlError.message}</div>
                      </div>
                      <button 
                        onClick={clearETLResults}
                        className="text-sm text-red-600 hover:text-red-800"
                      >
                        ✕
                      </button>
                    </div>
                  </div>
                )}
              </div>
              
              <div className="grid md:grid-cols-2 gap-8">
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-3">
                    What you can ask:
                  </h3>
                  <ul className="space-y-2 text-gray-700">
                    <li className="flex items-start space-x-2">
                      <span className="text-primary-500 mt-1">•</span>
                      <span><strong>Holdings:</strong> "What is SPY's exposure to AAPL?"</span>
                    </li>
                    <li className="flex items-start space-x-2">
                      <span className="text-primary-500 mt-1">•</span>
                      <span><strong>Overlaps:</strong> "Show overlap between QQQ and SPY"</span>
                    </li>
                    <li className="flex items-start space-x-2">
                      <span className="text-primary-500 mt-1">•</span>
                      <span><strong>Sectors:</strong> "What is QQQ's sector breakdown?"</span>
                    </li>
                    <li className="flex items-start space-x-2">
                      <span className="text-primary-500 mt-1">•</span>
                      <span><strong>Thresholds:</strong> "ETFs with 20%+ tech exposure"</span>
                    </li>
                  </ul>
                </div>
                
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-3">
                    Supported ETFs:
                  </h3>
                  <div className="grid grid-cols-2 gap-2">
                    <div className="bg-white border border-gray-200 rounded p-3">
                      <div className="font-medium text-gray-900">SPY</div>
                      <div className="text-sm text-gray-600">S&P 500</div>
                    </div>
                    <div className="bg-white border border-gray-200 rounded p-3">
                      <div className="font-medium text-gray-900">QQQ</div>
                      <div className="text-sm text-gray-600">Nasdaq 100</div>
                    </div>
                    <div className="bg-white border border-gray-200 rounded p-3">
                      <div className="font-medium text-gray-900">IWM</div>
                      <div className="text-sm text-gray-600">Russell 2000</div>
                    </div>
                    <div className="bg-white border border-gray-200 rounded p-3">
                      <div className="font-medium text-gray-900">IJH</div>
                      <div className="text-sm text-gray-600">S&P Mid-Cap</div>
                    </div>
                    <div className="bg-white border border-gray-200 rounded p-3">
                      <div className="font-medium text-gray-900">IVE</div>
                      <div className="text-sm text-gray-600">S&P 500 Value</div>
                    </div>
                    <div className="bg-white border border-gray-200 rounded p-3">
                      <div className="font-medium text-gray-900">IVW</div>
                      <div className="text-sm text-gray-600">S&P 500 Growth</div>
                    </div>
                  </div>
                </div>
              </div>

              <div className="mt-8 p-4 bg-white/80 border border-blue-200 rounded">
                <h4 className="font-medium text-gray-900 mb-2">How it works:</h4>
                <p className="text-sm text-gray-700">
                  Your questions are processed through a 7-step GraphRAG pipeline: text preprocessing, 
                  entity grounding, intent classification, parameter fulfillment, Cypher execution, 
                  and LLM answer synthesis. Each response includes both structured data 
                  and a natural language explanation.
                </p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default Home