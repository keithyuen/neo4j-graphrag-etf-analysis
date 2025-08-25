import { useState, useEffect } from 'react'
import CytoscapeGraph from '../components/graph/CytoscapeGraph'
import GraphControls from '../components/graph/GraphControls'
import GraphLegend from '../components/graph/GraphLegend'
import { useGraph } from '../hooks/useGraph'
import { useGraphSettings } from '../hooks/useLocalStorage'

function Graph() {
  const { loading, data, error, settings, loadData, updateSettings } = useGraph()
  const { settings: savedSettings, updateSetting } = useGraphSettings()
  const [selectedNode, setSelectedNode] = useState(null)
  const [selectedEdge, setSelectedEdge] = useState(null)

  // Initialize with saved settings
  useEffect(() => {
    updateSettings({
      ticker: savedSettings.lastTicker || 'SPY',
      topN: savedSettings.lastTopN || 10,
      edgeWeightThreshold: savedSettings.lastEdgeThreshold || 0.0,
      layout: savedSettings.lastLayout || 'cose-bilkent'
    })
  }, [savedSettings, updateSettings])

  // Auto-load data when component mounts
  useEffect(() => {
    if (settings.ticker) {
      handleLoadData(settings.ticker, settings.topN, settings.edgeWeightThreshold)
    }
  }, []) // Only run on mount

  const handleSettingsChange = (newSettings) => {
    updateSettings(newSettings)
    
    // Save to localStorage
    updateSetting('lastTicker', newSettings.ticker)
    updateSetting('lastTopN', newSettings.topN)
    updateSetting('lastEdgeThreshold', newSettings.edgeWeightThreshold)
    updateSetting('lastLayout', newSettings.layout)
  }

  const handleLoadData = async (ticker, topN, threshold) => {
    await loadData(ticker, topN, threshold)
  }

  const handleNodeClick = (node) => {
    setSelectedNode(node)
    setSelectedEdge(null)
    console.log('Node clicked:', node)
  }

  const handleEdgeClick = (edge) => {
    setSelectedEdge(edge)
    setSelectedNode(null)
    console.log('Edge clicked:', edge)
  }

  const handleBackgroundClick = () => {
    setSelectedNode(null)
    setSelectedEdge(null)
  }

  return (
    <div className="h-screen bg-gray-50 flex">
      {/* Sidebar */}
      <div className="w-80 flex-shrink-0 bg-white border-r border-gray-200 overflow-y-auto">
        <div className="p-6 space-y-6">
          {/* Header */}
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Graph Visualization</h1>
            <p className="text-sm text-gray-600 mt-2">
              Interactive exploration of ETF holdings and sector relationships
            </p>
          </div>

          {/* Controls */}
          <GraphControls
            settings={settings}
            onSettingsChange={handleSettingsChange}
            onLoadData={handleLoadData}
            loading={loading}
          />

          {/* Legend */}
          <GraphLegend />

          {/* Error Display */}
          {error && (
            <div className="alert alert-error">
              <div className="font-medium">Error Loading Graph</div>
              <div className="text-sm mt-1">{error.message}</div>
            </div>
          )}

          {/* Stats */}
          {data.nodes.length > 0 && (
            <div className="card">
              <div className="card-header">
                <h3 className="text-sm font-semibold text-gray-900">Graph Statistics</h3>
              </div>
              <div className="card-body space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-600">Total Nodes:</span>
                  <span className="font-medium">{data.nodes.length}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Total Edges:</span>
                  <span className="font-medium">{data.edges.length}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">ETF:</span>
                  <span className="font-medium">{settings.ticker}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Layout:</span>
                  <span className="font-medium">{settings.layout}</span>
                </div>
              </div>
            </div>
          )}

          {/* Selection Info */}
          {(selectedNode || selectedEdge) && (
            <div className="card">
              <div className="card-header">
                <h3 className="text-sm font-semibold text-gray-900">Selection Details</h3>
              </div>
              <div className="card-body">
                {selectedNode && (
                  <div className="space-y-2 text-sm">
                    <div>
                      <span className="text-gray-600">Type:</span>
                      <span className="ml-2 font-medium">{selectedNode.type}</span>
                    </div>
                    <div>
                      <span className="text-gray-600">Label:</span>
                      <span className="ml-2 font-medium">{selectedNode.label}</span>
                    </div>
                    {selectedNode.name && selectedNode.name !== selectedNode.label && (
                      <div>
                        <span className="text-gray-600">Name:</span>
                        <span className="ml-2 font-medium">{selectedNode.name}</span>
                      </div>
                    )}
                    {selectedNode.ticker && (
                      <div>
                        <span className="text-gray-600">Ticker:</span>
                        <span className="ml-2 font-medium">{selectedNode.ticker}</span>
                      </div>
                    )}
                    {selectedNode.symbol && (
                      <div>
                        <span className="text-gray-600">Symbol:</span>
                        <span className="ml-2 font-medium">{selectedNode.symbol}</span>
                      </div>
                    )}
                  </div>
                )}

                {selectedEdge && (
                  <div className="space-y-2 text-sm">
                    <div>
                      <span className="text-gray-600">Type:</span>
                      <span className="ml-2 font-medium">{selectedEdge.type}</span>
                    </div>
                    {selectedEdge.weight !== undefined && (
                      <div>
                        <span className="text-gray-600">Weight:</span>
                        <span className="ml-2 font-medium">{(selectedEdge.weight * 100).toFixed(3)}%</span>
                      </div>
                    )}
                    {selectedEdge.shares && (
                      <div>
                        <span className="text-gray-600">Shares:</span>
                        <span className="ml-2 font-medium">{selectedEdge.shares.toLocaleString()}</span>
                      </div>
                    )}
                    <div>
                      <span className="text-gray-600">Source:</span>
                      <span className="ml-2 font-medium">{selectedEdge.source}</span>
                    </div>
                    <div>
                      <span className="text-gray-600">Target:</span>
                      <span className="ml-2 font-medium">{selectedEdge.target}</span>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Main Graph Area */}
      <div className="flex-1 relative">
        <CytoscapeGraph
          data={data}
          layout={settings.layout}
          edgeWeightThreshold={settings.edgeWeightThreshold}
          loading={loading}
          onNodeClick={handleNodeClick}
          onEdgeClick={handleEdgeClick}
          onBackgroundClick={handleBackgroundClick}
          className="w-full h-full"
        />

        {/* Floating Help */}
        <div className="absolute top-4 left-4 bg-white/90 backdrop-blur border border-gray-200 rounded-lg p-3 max-w-sm">
          <h4 className="text-sm font-medium text-gray-900 mb-2">Quick Help</h4>
          <ul className="text-xs text-gray-600 space-y-1">
            <li>• Use the sidebar to configure ETF, holdings count, and layout</li>
            <li>• Click on nodes and edges to see detailed information</li>
            <li>• Drag to pan, scroll to zoom, or use the controls</li>
            <li>• Adjust the edge weight threshold to filter connections</li>
          </ul>
        </div>
      </div>
    </div>
  )
}

export default Graph