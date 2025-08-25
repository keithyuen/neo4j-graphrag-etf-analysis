import { useState } from 'react'
import { Play, RefreshCw, Settings, Sliders } from 'lucide-react'
import LoadingSpinner from '../common/LoadingSpinner'
import { ALLOWED_TICKERS, GRAPH_LAYOUTS, UI_SETTINGS } from '../../utils/constants'
import clsx from 'clsx'

function GraphControls({ 
  settings,
  onSettingsChange,
  onLoadData,
  loading = false,
  className = ''
}) {
  const [localSettings, setLocalSettings] = useState(settings)
  const [isExpanded, setIsExpanded] = useState(true)

  const handleSettingChange = (key, value) => {
    const newSettings = { ...localSettings, [key]: value }
    setLocalSettings(newSettings)
    onSettingsChange?.(newSettings)
  }

  const handleLoadData = () => {
    onLoadData?.(localSettings.ticker, localSettings.topN, localSettings.edgeWeightThreshold)
  }

  return (
    <div className={clsx('card h-fit', className)}>
      <div 
        className="card-header cursor-pointer select-none"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Settings className="w-5 h-5 text-gray-500" />
            <h3 className="text-lg font-semibold text-gray-900">Graph Controls</h3>
          </div>
          <Sliders className={clsx('w-4 h-4 text-gray-400 transition-transform', isExpanded && 'rotate-180')} />
        </div>
      </div>

      {isExpanded && (
        <div className="card-body space-y-6">
          {/* ETF Selection */}
          <div>
            <label className="form-label">ETF Ticker</label>
            <select
              value={localSettings.ticker}
              onChange={(e) => handleSettingChange('ticker', e.target.value)}
              className="form-select"
              disabled={loading}
            >
              {ALLOWED_TICKERS.map(ticker => (
                <option key={ticker} value={ticker}>{ticker}</option>
              ))}
            </select>
            <p className="text-xs text-gray-500 mt-1">
              Select an ETF to visualize its holdings
            </p>
          </div>

          {/* Top N Holdings */}
          <div>
            <label className="form-label">
              Top Holdings: {localSettings.topN}
            </label>
            <div className="space-y-2">
              <input
                type="range"
                min={UI_SETTINGS.minTopN}
                max={UI_SETTINGS.maxTopN}
                value={localSettings.topN}
                onChange={(e) => handleSettingChange('topN', parseInt(e.target.value))}
                className="w-full"
                disabled={loading}
              />
              <div className="flex justify-between text-xs text-gray-500">
                <span>{UI_SETTINGS.minTopN}</span>
                <span>{UI_SETTINGS.maxTopN}</span>
              </div>
            </div>
            <p className="text-xs text-gray-500 mt-1">
              Number of top holdings to display
            </p>
          </div>

          {/* Edge Weight Threshold */}
          <div>
            <label className="form-label">
              Edge Weight Threshold: {(localSettings.edgeWeightThreshold * 100).toFixed(1)}%
            </label>
            <div className="space-y-2">
              <input
                type="range"
                min={UI_SETTINGS.minEdgeThreshold}
                max={UI_SETTINGS.maxEdgeThreshold}
                step={0.005}
                value={localSettings.edgeWeightThreshold}
                onChange={(e) => handleSettingChange('edgeWeightThreshold', parseFloat(e.target.value))}
                className="w-full"
                disabled={loading}
              />
              <div className="flex justify-between text-xs text-gray-500">
                <span>0%</span>
                <span>100%</span>
              </div>
            </div>
            <p className="text-xs text-gray-500 mt-1">
              Hide edges below this weight threshold
            </p>
          </div>

          {/* Layout Selection */}
          <div>
            <label className="form-label">Graph Layout</label>
            <select
              value={localSettings.layout}
              onChange={(e) => handleSettingChange('layout', e.target.value)}
              className="form-select"
              disabled={loading}
            >
              {GRAPH_LAYOUTS.map(layout => (
                <option key={layout.value} value={layout.value}>
                  {layout.label}
                </option>
              ))}
            </select>
            <p className="text-xs text-gray-500 mt-1">
              Algorithm for positioning nodes
            </p>
          </div>

          {/* Action Buttons */}
          <div className="space-y-3 pt-4 border-t border-gray-200">
            <button
              onClick={handleLoadData}
              disabled={loading}
              className="btn-primary w-full flex items-center justify-center space-x-2"
            >
              {loading ? (
                <>
                  <LoadingSpinner size="sm" color="white" />
                  <span>Loading...</span>
                </>
              ) : (
                <>
                  <Play className="w-4 h-4" />
                  <span>Load Graph</span>
                </>
              )}
            </button>

            <button
              onClick={() => window.location.reload()}
              disabled={loading}
              className="btn-outline w-full flex items-center justify-center space-x-2"
            >
              <RefreshCw className="w-4 h-4" />
              <span>Reset All</span>
            </button>
          </div>

          {/* Quick Presets */}
          <div className="pt-4 border-t border-gray-200">
            <div className="text-sm font-medium text-gray-700 mb-3">Quick Presets</div>
            <div className="grid grid-cols-2 gap-2">
              <button
                onClick={() => {
                  handleSettingChange('ticker', 'SPY')
                  handleSettingChange('topN', 10)
                  handleSettingChange('edgeWeightThreshold', 0.01)
                }}
                className="btn-outline text-xs py-2"
                disabled={loading}
              >
                SPY Top 10
              </button>
              <button
                onClick={() => {
                  handleSettingChange('ticker', 'QQQ')
                  handleSettingChange('topN', 15)
                  handleSettingChange('edgeWeightThreshold', 0.02)
                }}
                className="btn-outline text-xs py-2"
                disabled={loading}
              >
                QQQ Top 15
              </button>
              <button
                onClick={() => {
                  handleSettingChange('topN', 25)
                  handleSettingChange('edgeWeightThreshold', 0.005)
                }}
                className="btn-outline text-xs py-2"
                disabled={loading}
              >
                Detailed View
              </button>
              <button
                onClick={() => {
                  handleSettingChange('topN', 5)
                  handleSettingChange('edgeWeightThreshold', 0.05)
                }}
                className="btn-outline text-xs py-2"
                disabled={loading}
              >
                Simple View
              </button>
            </div>
          </div>

          {/* Current Settings Summary */}
          <div className="pt-4 border-t border-gray-200">
            <div className="text-sm font-medium text-gray-700 mb-2">Current Settings</div>
            <div className="text-xs text-gray-600 space-y-1">
              <div>ETF: <span className="font-medium">{localSettings.ticker}</span></div>
              <div>Holdings: <span className="font-medium">{localSettings.topN}</span></div>
              <div>Threshold: <span className="font-medium">{(localSettings.edgeWeightThreshold * 100).toFixed(1)}%</span></div>
              <div>Layout: <span className="font-medium">{GRAPH_LAYOUTS.find(l => l.value === localSettings.layout)?.label}</span></div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default GraphControls