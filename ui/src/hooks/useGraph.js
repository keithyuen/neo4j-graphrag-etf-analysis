import { useState, useCallback, useRef, useEffect } from 'react'
import { apiHooks } from '../services/api'
import { DEFAULT_GRAPH_LAYOUT, UI_SETTINGS } from '../utils/constants'

/**
 * Hook for managing graph visualization state and data
 */
export function useGraph() {
  const [loading, setLoading] = useState(false)
  const [data, setData] = useState({ nodes: [], edges: [] })
  const [error, setError] = useState(null)
  const [settings, setSettings] = useState({
    ticker: 'SPY',
    topN: UI_SETTINGS.defaultTopN,
    edgeWeightThreshold: UI_SETTINGS.defaultEdgeThreshold,
    layout: DEFAULT_GRAPH_LAYOUT
  })

  const loadData = useCallback(async (ticker, topN, threshold) => {
    if (!ticker?.trim()) {
      setError({ message: 'Ticker is required' })
      return
    }

    setError(null)
    
    try {
      const result = await apiHooks.loadGraphData(ticker, topN, threshold, {
        onStart: () => setLoading(true),
        onSuccess: (data) => {
          setData({
            nodes: data.nodes || [],
            edges: data.edges || []
          })
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

  const updateSettings = useCallback((newSettings) => {
    setSettings(prev => ({ ...prev, ...newSettings }))
  }, [])

  const refreshData = useCallback(() => {
    return loadData(settings.ticker, settings.topN, settings.edgeWeightThreshold)
  }, [loadData, settings])

  const clearData = useCallback(() => {
    setData({ nodes: [], edges: [] })
    setError(null)
  }, [])

  return {
    loading,
    data,
    error,
    settings,
    loadData,
    updateSettings,
    refreshData,
    clearData
  }
}

/**
 * Hook for managing Cytoscape instance and interactions
 */
export function useCytoscape() {
  const cyRef = useRef(null)
  const cyInstance = useRef(null)
  const [selectedNode, setSelectedNode] = useState(null)
  const [selectedEdge, setSelectedEdge] = useState(null)

  const initializeCytoscape = useCallback((data, layout, options = {}) => {
    if (!cyRef.current || !data.nodes.length) return

    // Destroy existing instance
    if (cyInstance.current) {
      cyInstance.current.destroy()
    }

    // Import Cytoscape dynamically
    import('cytoscape').then(({ default: cytoscape }) => {
      // Import layout extensions
      Promise.all([
        import('cytoscape-cose-bilkent'),
        import('cytoscape-fcose'),
        import('cytoscape-cola')
      ]).then(([coseBilkent, fcose, cola]) => {
        // Register extensions
        cytoscape.use(coseBilkent.default)
        cytoscape.use(fcose.default)
        cytoscape.use(cola.default)

        // Create new instance
        cyInstance.current = cytoscape({
          container: cyRef.current,
          elements: {
            nodes: data.nodes.map(node => ({
              data: { id: node.id, label: node.label, type: node.type, ...node.properties },
              classes: node.type
            })),
            edges: data.edges.map(edge => ({
              data: { 
                id: edge.id, 
                source: edge.source, 
                target: edge.target, 
                type: edge.type,
                weight: edge.properties?.weight || 0,
                ...edge.properties 
              },
              classes: edge.type
            }))
          },
          style: getCytoscapeStyles(),
          layout: {
            name: layout,
            animate: true,
            animationDuration: UI_SETTINGS.animationDuration,
            ...options.layoutOptions
          },
          ...options.cytoscapeOptions
        })

        // Add event listeners
        cyInstance.current.on('tap', 'node', (event) => {
          const node = event.target.data()
          setSelectedNode(node)
          setSelectedEdge(null)
          options.onNodeClick?.(node)
        })

        cyInstance.current.on('tap', 'edge', (event) => {
          const edge = event.target.data()
          setSelectedEdge(edge)
          setSelectedNode(null)
          options.onEdgeClick?.(edge)
        })

        cyInstance.current.on('tap', (event) => {
          if (event.target === cyInstance.current) {
            setSelectedNode(null)
            setSelectedEdge(null)
            options.onBackgroundClick?.()
          }
        })
      })
    })
  }, [])

  const updateLayout = useCallback((layout, options = {}) => {
    if (cyInstance.current) {
      cyInstance.current.layout({
        name: layout,
        animate: true,
        animationDuration: UI_SETTINGS.animationDuration,
        ...options
      }).run()
    }
  }, [])

  const fitToView = useCallback(() => {
    if (cyInstance.current) {
      cyInstance.current.fit(null, 50)
    }
  }, [])

  const resetZoom = useCallback(() => {
    if (cyInstance.current) {
      cyInstance.current.zoom(1)
      cyInstance.current.center()
    }
  }, [])

  const exportImage = useCallback((format = 'png') => {
    if (cyInstance.current) {
      return cyInstance.current.png({
        output: 'blob',
        bg: 'white',
        full: true
      })
    }
    return null
  }, [])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (cyInstance.current) {
        cyInstance.current.destroy()
      }
    }
  }, [])

  return {
    cyRef,
    cyInstance: cyInstance.current,
    selectedNode,
    selectedEdge,
    initializeCytoscape,
    updateLayout,
    fitToView,
    resetZoom,
    exportImage,
    setSelectedNode,
    setSelectedEdge
  }
}

/**
 * Get Cytoscape styles for nodes and edges
 */
function getCytoscapeStyles() {
  return [
    // ETF nodes
    {
      selector: 'node.ETF',
      style: {
        'background-color': '#3B82F6',
        'color': '#FFFFFF',
        'label': 'data(label)',
        'text-valign': 'center',
        'text-halign': 'center',
        'font-size': '12px',
        'font-weight': 'bold',
        'width': '60px',
        'height': '60px',
        'border-width': 2,
        'border-color': '#1D4ED8'
      }
    },
    // Company nodes
    {
      selector: 'node.Company',
      style: {
        'background-color': '#10B981',
        'color': '#FFFFFF',
        'label': 'data(label)',
        'text-valign': 'center',
        'text-halign': 'center',
        'font-size': '10px',
        'width': '40px',
        'height': '40px',
        'border-width': 1,
        'border-color': '#047857'
      }
    },
    // Sector nodes
    {
      selector: 'node.Sector',
      style: {
        'background-color': '#F59E0B',
        'color': '#FFFFFF',
        'label': 'data(label)',
        'text-valign': 'center',
        'text-halign': 'center',
        'font-size': '8px',
        'width': '80px',
        'height': '30px',
        'shape': 'rectangle',
        'border-width': 1,
        'border-color': '#D97706'
      }
    },
    // HOLDS edges
    {
      selector: 'edge.HOLDS',
      style: {
        'width': 'mapData(weight, 0, 1, 1, 8)',
        'line-color': '#6B7280',
        'target-arrow-color': '#6B7280',
        'target-arrow-shape': 'triangle',
        'curve-style': 'bezier',
        'opacity': 0.8
      }
    },
    // IN_SECTOR edges
    {
      selector: 'edge.IN_SECTOR',
      style: {
        'width': 2,
        'line-color': '#9CA3AF',
        'line-style': 'dashed',
        'curve-style': 'bezier',
        'opacity': 0.6
      }
    },
    // Selected states
    {
      selector: 'node:selected',
      style: {
        'border-width': 4,
        'border-color': '#EF4444',
        'z-index': 10
      }
    },
    {
      selector: 'edge:selected',
      style: {
        'line-color': '#EF4444',
        'target-arrow-color': '#EF4444',
        'width': 'mapData(weight, 0, 1, 3, 12)',
        'z-index': 10
      }
    }
  ]
}