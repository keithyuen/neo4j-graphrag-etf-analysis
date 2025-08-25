import { Info, Eye, EyeOff } from 'lucide-react'
import { useState } from 'react'
import { NODE_TYPES } from '../../utils/constants'
import clsx from 'clsx'

function GraphLegend({ className = '' }) {
  const [isVisible, setIsVisible] = useState(true)
  const [isExpanded, setIsExpanded] = useState(false)

  if (!isVisible) {
    return (
      <button
        onClick={() => setIsVisible(true)}
        className={clsx('btn-outline !p-2', className)}
        title="Show Legend"
      >
        <Eye className="w-4 h-4" />
      </button>
    )
  }

  return (
    <div className={clsx('card', className)}>
      <div 
        className="card-header cursor-pointer select-none"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Info className="w-4 h-4 text-gray-500" />
            <h3 className="text-sm font-semibold text-gray-900">Graph Legend</h3>
          </div>
          
          <button
            onClick={(e) => {
              e.stopPropagation()
              setIsVisible(false)
            }}
            className="p-1 hover:bg-gray-100 rounded"
            title="Hide Legend"
          >
            <EyeOff className="w-3 h-3 text-gray-400" />
          </button>
        </div>
      </div>

      <div className="card-body space-y-4">
        {/* Node Types */}
        <div>
          <h4 className="text-xs font-medium text-gray-700 mb-2 uppercase tracking-wide">Node Types</h4>
          <div className="space-y-2">
            {Object.entries(NODE_TYPES).map(([type, config]) => (
              <div key={type} className="flex items-center space-x-3">
                <div 
                  className="w-4 h-4 rounded flex-shrink-0 border border-gray-300"
                  style={{ 
                    backgroundColor: config.color,
                    ...(type === 'Sector' && { borderRadius: '2px' })
                  }}
                />
                <div className="text-sm">
                  <div className="font-medium text-gray-900">{config.label}</div>
                  <div className="text-xs text-gray-500">
                    {getNodeTypeDescription(type)}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Edge Types */}
        <div>
          <h4 className="text-xs font-medium text-gray-700 mb-2 uppercase tracking-wide">Edge Types</h4>
          <div className="space-y-2">
            <div className="flex items-center space-x-3">
              <div className="flex-shrink-0">
                <svg width="20" height="8" viewBox="0 0 20 8">
                  <line x1="0" y1="4" x2="20" y2="4" stroke="#6B7280" strokeWidth="2" markerEnd="url(#arrow)" />
                  <defs>
                    <marker id="arrow" markerWidth="6" markerHeight="6" refX="5" refY="3" orient="auto" markerUnits="strokeWidth">
                      <path d="M0,0 L0,6 L6,3 z" fill="#6B7280" />
                    </marker>
                  </defs>
                </svg>
              </div>
              <div className="text-sm">
                <div className="font-medium text-gray-900">HOLDS</div>
                <div className="text-xs text-gray-500">ETF holds company shares</div>
              </div>
            </div>
            
            <div className="flex items-center space-x-3">
              <div className="flex-shrink-0">
                <svg width="20" height="8" viewBox="0 0 20 8">
                  <line x1="0" y1="4" x2="20" y2="4" stroke="#9CA3AF" strokeWidth="1" strokeDasharray="3,2" />
                </svg>
              </div>
              <div className="text-sm">
                <div className="font-medium text-gray-900">IN_SECTOR</div>
                <div className="text-xs text-gray-500">Company belongs to sector</div>
              </div>
            </div>
          </div>
        </div>

        {isExpanded && (
          <>
            {/* Edge Weights */}
            <div>
              <h4 className="text-xs font-medium text-gray-700 mb-2 uppercase tracking-wide">Edge Weights</h4>
              <div className="space-y-2">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-600">Thin edge</span>
                  <span className="text-gray-900">Low weight (&lt; 1%)</span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-600">Medium edge</span>
                  <span className="text-gray-900">Medium weight (1-5%)</span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-600">Thick edge</span>
                  <span className="text-gray-900">High weight (&gt; 5%)</span>
                </div>
              </div>
            </div>

            {/* Interaction Guide */}
            <div>
              <h4 className="text-xs font-medium text-gray-700 mb-2 uppercase tracking-wide">Interactions</h4>
              <div className="space-y-1 text-xs text-gray-600">
                <div>• Click nodes/edges for details</div>
                <div>• Hover for quick info</div>
                <div>• Drag to pan the graph</div>
                <div>• Scroll to zoom in/out</div>
                <div>• Use controls to fit/reset view</div>
              </div>
            </div>

            {/* Color Coding */}
            <div>
              <h4 className="text-xs font-medium text-gray-700 mb-2 uppercase tracking-wide">Color Guide</h4>
              <div className="space-y-1 text-xs text-gray-600">
                <div className="flex items-center space-x-2">
                  <div className="w-3 h-3 bg-blue-500 rounded"></div>
                  <span>Blue = ETFs (Investment funds)</span>
                </div>
                <div className="flex items-center space-x-2">
                  <div className="w-3 h-3 bg-green-500 rounded"></div>
                  <span>Green = Companies (Individual stocks)</span>
                </div>
                <div className="flex items-center space-x-2">
                  <div className="w-3 h-3 bg-yellow-500 rounded"></div>
                  <span>Yellow = Sectors (Industry categories)</span>
                </div>
                <div className="flex items-center space-x-2">
                  <div className="w-3 h-3 bg-red-500 rounded border-2 border-red-600"></div>
                  <span>Red border = Selected element</span>
                </div>
              </div>
            </div>
          </>
        )}

        {/* Expand/Collapse Button */}
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="btn-outline w-full text-xs"
        >
          {isExpanded ? 'Show Less' : 'Show More'}
        </button>
      </div>
    </div>
  )
}

function getNodeTypeDescription(type) {
  switch (type) {
    case 'ETF':
      return 'Exchange-traded funds'
    case 'Company':
      return 'Individual companies/stocks'
    case 'Sector':
      return 'Industry sectors'
    default:
      return ''
  }
}

export default GraphLegend