import { useEffect, useRef, useState } from 'react'
import { ZoomIn, ZoomOut, Maximize, Download, RotateCcw } from 'lucide-react'
import LoadingSpinner from '../common/LoadingSpinner'
import { useCytoscape } from '../../hooks/useGraph'
import { formatEdgeWeight, formatNodeLabel } from '../../utils/formatters'
import { UI_SETTINGS } from '../../utils/constants'
import clsx from 'clsx'

function CytoscapeGraph({ 
  data, 
  layout = 'cose-bilkent',
  edgeWeightThreshold = 0,
  loading = false,
  onNodeClick,
  onEdgeClick,
  onBackgroundClick,
  className = ''
}) {
  const [isInitialized, setIsInitialized] = useState(false)
  const [tooltipData, setTooltipData] = useState(null)
  const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 })

  const {
    cyRef,
    cyInstance,
    selectedNode,
    selectedEdge,
    initializeCytoscape,
    updateLayout,
    fitToView,
    resetZoom,
    exportImage
  } = useCytoscape()

  // Filter data by edge weight threshold
  const filteredData = {
    nodes: data.nodes || [],
    edges: (data.edges || []).filter(edge => {
      const weight = edge.properties?.weight || 0
      return weight >= edgeWeightThreshold
    })
  }

  // Initialize Cytoscape when data changes
  useEffect(() => {
    if (filteredData.nodes.length > 0) {
      initializeCytoscape(filteredData, layout, {
        onNodeClick: (node) => {
          onNodeClick?.(node)
          setTooltipData(null)
        },
        onEdgeClick: (edge) => {
          onEdgeClick?.(edge)
          setTooltipData(null)
        },
        onBackgroundClick: () => {
          onBackgroundClick?.()
          setTooltipData(null)
        }
      })
      setIsInitialized(true)
    }
  }, [filteredData, layout, initializeCytoscape, onNodeClick, onEdgeClick, onBackgroundClick])

  // Update layout when layout prop changes
  useEffect(() => {
    if (cyInstance && isInitialized) {
      updateLayout(layout)
    }
  }, [layout, cyInstance, isInitialized, updateLayout])

  // Add hover tooltips
  useEffect(() => {
    if (!cyInstance) return

    const handleMouseOver = (event) => {
      const target = event.target
      const isNode = target.group && target.group() === 'nodes'
      const isEdge = target.group && target.group() === 'edges'

      if (isNode || isEdge) {
        const data = target.data()
        setTooltipData({
          type: isNode ? 'node' : 'edge',
          data: data,
          x: event.renderedPosition.x || event.position.x,
          y: event.renderedPosition.y || event.position.y
        })
      }
    }

    const handleMouseOut = () => {
      setTooltipData(null)
    }

    const handleMouseMove = (event) => {
      setMousePosition({
        x: event.originalEvent.clientX,
        y: event.originalEvent.clientY
      })
    }

    cyInstance.on('mouseover', 'node,edge', handleMouseOver)
    cyInstance.on('mouseout', 'node,edge', handleMouseOut)
    cyInstance.on('mousemove', handleMouseMove)

    return () => {
      if (cyInstance) {
        cyInstance.off('mouseover', 'node,edge', handleMouseOver)
        cyInstance.off('mouseout', 'node,edge', handleMouseOut)
        cyInstance.off('mousemove', handleMouseMove)
      }
    }
  }, [cyInstance])

  const handleZoomIn = () => {
    if (cyInstance) {
      const currentZoom = cyInstance.zoom()
      cyInstance.zoom(currentZoom * 1.2)
    }
  }

  const handleZoomOut = () => {
    if (cyInstance) {
      const currentZoom = cyInstance.zoom()
      cyInstance.zoom(currentZoom * 0.8)
    }
  }

  const handleExportImage = async () => {
    try {
      const blob = await exportImage('png')
      if (blob) {
        const url = URL.createObjectURL(blob)
        const link = document.createElement('a')
        link.href = url
        link.download = `etf-graph-${new Date().toISOString().split('T')[0]}.png`
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
        URL.revokeObjectURL(url)
      }
    } catch (error) {
      console.error('Failed to export image:', error)
    }
  }

  if (loading) {
    return (
      <div className={clsx('relative bg-gray-50 border border-gray-200 rounded-lg flex items-center justify-center', className)}>
        <LoadingSpinner size="lg" label="Loading graph data..." />
      </div>
    )
  }

  if (!filteredData.nodes.length) {
    return (
      <div className={clsx('relative bg-gray-50 border border-gray-200 rounded-lg flex items-center justify-center', className)}>
        <div className="text-center">
          <div className="w-16 h-16 bg-gray-200 rounded-lg flex items-center justify-center mx-auto mb-4">
            <Maximize className="w-8 h-8 text-gray-400" />
          </div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">No Graph Data</h3>
          <p className="text-gray-500 max-w-sm">
            Select an ETF and configure the settings to view the graph visualization.
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className={clsx('relative bg-white border border-gray-200 rounded-lg overflow-hidden', className)}>
      {/* Graph Container */}
      <div 
        ref={cyRef} 
        className="w-full h-full min-h-[600px]"
        style={{ background: '#fafafa' }}
      />

      {/* Graph Controls */}
      <div className="absolute top-4 right-4 flex flex-col space-y-2">
        <button
          onClick={handleZoomIn}
          className="p-2 bg-white border border-gray-300 rounded shadow-sm hover:bg-gray-50 transition-colors"
          title="Zoom In"
        >
          <ZoomIn className="w-4 h-4" />
        </button>
        
        <button
          onClick={handleZoomOut}
          className="p-2 bg-white border border-gray-300 rounded shadow-sm hover:bg-gray-50 transition-colors"
          title="Zoom Out"
        >
          <ZoomOut className="w-4 h-4" />
        </button>
        
        <button
          onClick={fitToView}
          className="p-2 bg-white border border-gray-300 rounded shadow-sm hover:bg-gray-50 transition-colors"
          title="Fit to View"
        >
          <Maximize className="w-4 h-4" />
        </button>
        
        <button
          onClick={resetZoom}
          className="p-2 bg-white border border-gray-300 rounded shadow-sm hover:bg-gray-50 transition-colors"
          title="Reset Zoom"
        >
          <RotateCcw className="w-4 h-4" />
        </button>
        
        <button
          onClick={handleExportImage}
          className="p-2 bg-white border border-gray-300 rounded shadow-sm hover:bg-gray-50 transition-colors"
          title="Export Image"
        >
          <Download className="w-4 h-4" />
        </button>
      </div>

      {/* Graph Stats */}
      <div className="absolute bottom-4 left-4 bg-white/90 backdrop-blur border border-gray-200 rounded px-3 py-2 text-sm text-gray-600">
        <div className="flex items-center space-x-4">
          <span>{filteredData.nodes.length} nodes</span>
          <span>{filteredData.edges.length} edges</span>
          {edgeWeightThreshold > 0 && (
            <span>threshold: {(edgeWeightThreshold * 100).toFixed(1)}%</span>
          )}
        </div>
      </div>

      {/* Selection Info */}
      {(selectedNode || selectedEdge) && (
        <div className="absolute top-4 left-4 bg-white border border-gray-200 rounded-lg shadow-sm p-4 max-w-xs">
          {selectedNode && (
            <div>
              <div className="text-sm font-medium text-gray-900 mb-2">
                {selectedNode.type} Node
              </div>
              <div className="space-y-1 text-sm text-gray-600">
                <div><strong>Label:</strong> {selectedNode.label}</div>
                {selectedNode.name && selectedNode.name !== selectedNode.label && (
                  <div><strong>Name:</strong> {selectedNode.name}</div>
                )}
                {selectedNode.ticker && (
                  <div><strong>Ticker:</strong> {selectedNode.ticker}</div>
                )}
                {selectedNode.symbol && (
                  <div><strong>Symbol:</strong> {selectedNode.symbol}</div>
                )}
              </div>
            </div>
          )}
          
          {selectedEdge && (
            <div>
              <div className="text-sm font-medium text-gray-900 mb-2">
                {selectedEdge.type} Relationship
              </div>
              <div className="space-y-1 text-sm text-gray-600">
                {selectedEdge.weight !== undefined && (
                  <div><strong>Weight:</strong> {formatEdgeWeight(selectedEdge.weight)}</div>
                )}
                {selectedEdge.shares && (
                  <div><strong>Shares:</strong> {selectedEdge.shares.toLocaleString()}</div>
                )}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Hover Tooltip */}
      {tooltipData && (
        <div 
          className="absolute z-50 bg-gray-900 text-white text-xs rounded px-2 py-1 pointer-events-none"
          style={{
            left: mousePosition.x + 10,
            top: mousePosition.y - 30,
            transform: 'translate(-50%, 0)'
          }}
        >
          {tooltipData.type === 'node' ? (
            <div>
              <div className="font-medium">{formatNodeLabel(tooltipData.data)}</div>
              <div className="text-gray-300">{tooltipData.data.type}</div>
            </div>
          ) : (
            <div>
              <div className="font-medium">{tooltipData.data.type}</div>
              {tooltipData.data.weight !== undefined && (
                <div className="text-gray-300">
                  Weight: {formatEdgeWeight(tooltipData.data.weight)}
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default CytoscapeGraph