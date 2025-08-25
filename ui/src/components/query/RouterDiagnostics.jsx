import { useState } from 'react'
import { ChevronDown, ChevronRight, Settings, Clock, Database, Brain, Target } from 'lucide-react'
import { formatExecutionTime, formatConfidence, formatEntityName } from '../../utils/formatters'
import { INTENT_TYPES } from '../../utils/constants'
import clsx from 'clsx'

function RouterDiagnostics({ 
  intent, 
  entities = [], 
  metadata = {}, 
  cypher = '',
  className = '' 
}) {
  const [isExpanded, setIsExpanded] = useState(false)
  const [activeTab, setActiveTab] = useState('overview')

  if (!intent && !entities.length && !Object.keys(metadata).length) {
    return null
  }

  const tabs = [
    { id: 'overview', label: 'Overview', icon: Target },
    { id: 'entities', label: 'Entities', icon: Brain },
    { id: 'timing', label: 'Performance', icon: Clock },
    { id: 'cypher', label: 'Query', icon: Database }
  ]

  return (
    <div className={clsx('card', className)}>
      <div 
        className="card-header cursor-pointer select-none hover:bg-gray-50 transition-colors"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Settings className="w-5 h-5 text-gray-500" />
            <h3 className="text-lg font-semibold text-gray-900">Pipeline Diagnostics</h3>
            <span className="badge badge-primary">Debug Info</span>
          </div>
          
          <div className="flex items-center space-x-2">
            {metadata.confidence !== undefined && (
              <span className="text-sm text-gray-500">
                Confidence: {formatConfidence(metadata.confidence)}
              </span>
            )}
            {isExpanded ? (
              <ChevronDown className="w-5 h-5 text-gray-400" />
            ) : (
              <ChevronRight className="w-5 h-5 text-gray-400" />
            )}
          </div>
        </div>
      </div>

      {isExpanded && (
        <div className="border-t border-gray-200">
          {/* Tab Navigation */}
          <div className="flex border-b border-gray-200 bg-gray-50">
            {tabs.map((tab) => {
              const Icon = tab.icon
              const isActive = activeTab === tab.id
              
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={clsx(
                    'flex items-center space-x-2 px-4 py-3 text-sm font-medium border-b-2 transition-colors',
                    isActive
                      ? 'border-primary-500 text-primary-700 bg-white'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:bg-gray-100'
                  )}
                >
                  <Icon className="w-4 h-4" />
                  <span>{tab.label}</span>
                </button>
              )
            })}
          </div>

          {/* Tab Content */}
          <div className="card-body">
            {activeTab === 'overview' && (
              <OverviewTab intent={intent} metadata={metadata} entities={entities} />
            )}
            
            {activeTab === 'entities' && (
              <EntitiesTab entities={entities} />
            )}
            
            {activeTab === 'timing' && (
              <TimingTab timing={metadata.timing} metadata={metadata} />
            )}
            
            {activeTab === 'cypher' && (
              <CypherTab cypher={cypher} metadata={metadata} />
            )}
          </div>
        </div>
      )}
    </div>
  )
}

function OverviewTab({ intent, metadata, entities }) {
  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-blue-50 rounded-lg p-4">
          <div className="text-sm font-medium text-blue-900">Intent Classification</div>
          <div className="text-lg font-bold text-blue-700 mt-1">
            {INTENT_TYPES[intent] || intent || 'Unknown'}
          </div>
          {metadata.confidence !== undefined && (
            <div className="text-sm text-blue-600 mt-1">
              {formatConfidence(metadata.confidence)} confidence
            </div>
          )}
        </div>

        <div className="bg-green-50 rounded-lg p-4">
          <div className="text-sm font-medium text-green-900">Entities Found</div>
          <div className="text-lg font-bold text-green-700 mt-1">
            {entities.length}
          </div>
          <div className="text-sm text-green-600 mt-1">
            {getEntitySummary(entities)}
          </div>
        </div>

        <div className="bg-purple-50 rounded-lg p-4">
          <div className="text-sm font-medium text-purple-900">Pipeline Version</div>
          <div className="text-lg font-bold text-purple-700 mt-1">
            {metadata.pipeline_version || '1.0.0'}
          </div>
          <div className="text-sm text-purple-600 mt-1">
            {metadata.cache_hit ? 'Cache hit' : 'Fresh result'}
          </div>
        </div>
      </div>

      {metadata.timing && (
        <div className="bg-gray-50 rounded-lg p-4">
          <div className="text-sm font-medium text-gray-900 mb-2">Total Execution Time</div>
          <div className="text-2xl font-bold text-gray-700">
            {formatExecutionTime(metadata.timing.total_pipeline)}
          </div>
        </div>
      )}
    </div>
  )
}

function EntitiesTab({ entities }) {
  const groupedEntities = entities.reduce((acc, entity) => {
    const type = entity.type
    if (!acc[type]) acc[type] = []
    acc[type].push(entity)
    return acc
  }, {})

  return (
    <div className="space-y-4">
      {Object.entries(groupedEntities).map(([type, typeEntities]) => (
        <div key={type} className="border border-gray-200 rounded-lg overflow-hidden">
          <div className="bg-gray-50 px-4 py-2 border-b border-gray-200">
            <h4 className="font-medium text-gray-900">{type} Entities ({typeEntities.length})</h4>
          </div>
          <div className="p-4">
            <div className="grid gap-3">
              {typeEntities.map((entity, index) => (
                <div key={index} className="flex items-center justify-between p-3 bg-white border border-gray-200 rounded">
                  <div>
                    <div className="font-medium text-gray-900">
                      {formatEntityName(entity)}
                    </div>
                    {entity.properties && Object.keys(entity.properties).length > 0 && (
                      <div className="text-sm text-gray-500 mt-1">
                        {Object.entries(entity.properties).map(([key, value]) => (
                          <span key={key} className="mr-3">
                            {key}: {String(value)}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                  <div className="text-sm text-gray-500">
                    {formatConfidence(entity.confidence)}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      ))}

      {entities.length === 0 && (
        <div className="text-center py-8 text-gray-500">
          No entities were identified in the query.
        </div>
      )}
    </div>
  )
}

function TimingTab({ timing, metadata }) {
  const timingData = timing || {}
  const steps = [
    { key: 'preprocessing', label: 'Text Preprocessing' },
    { key: 'entity_grounding', label: 'Entity Grounding' },
    { key: 'intent_classification', label: 'Intent Classification' },
    { key: 'parameter_fulfillment', label: 'Parameter Fulfillment' },
    { key: 'cypher_execution', label: 'Cypher Execution' },
    { key: 'llm_synthesis', label: 'LLM Synthesis' },
    { key: 'total_pipeline', label: 'Total Pipeline' }
  ]

  const maxTime = Math.max(...Object.values(timingData).filter(v => typeof v === 'number'))

  return (
    <div className="space-y-4">
      {steps.map((step) => {
        const time = timingData[step.key]
        if (time === undefined) return null

        const percentage = maxTime > 0 ? (time / maxTime) * 100 : 0

        return (
          <div key={step.key} className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-gray-900">{step.label}</span>
              <span className="text-sm text-gray-600">{formatExecutionTime(time)}</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className={clsx(
                  'h-2 rounded-full',
                  step.key === 'total_pipeline' ? 'bg-primary-600' : 'bg-primary-400'
                )}
                style={{ width: `${percentage}%` }}
              />
            </div>
          </div>
        )
      })}

      <div className="mt-6 p-4 bg-gray-50 rounded-lg">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
          {metadata.node_count !== undefined && (
            <div>
              <span className="text-gray-600">Nodes processed:</span>
              <span className="ml-2 font-medium">{metadata.node_count}</span>
            </div>
          )}
          {metadata.edge_count !== undefined && (
            <div>
              <span className="text-gray-600">Edges processed:</span>
              <span className="ml-2 font-medium">{metadata.edge_count}</span>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

function CypherTab({ cypher, metadata }) {
  return (
    <div className="space-y-4">
      <div className="bg-gray-900 rounded-lg p-4">
        <div className="text-xs text-gray-400 mb-2">Executed Cypher Query</div>
        <pre className="text-sm text-gray-100 overflow-x-auto whitespace-pre-wrap font-mono">
          {cypher || 'No query executed'}
        </pre>
      </div>

      {metadata && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="bg-blue-50 rounded-lg p-4">
            <div className="text-sm font-medium text-blue-900">Execution Time</div>
            <div className="text-lg font-bold text-blue-700 mt-1">
              {formatExecutionTime(metadata.timing?.cypher_execution)}
            </div>
          </div>

          <div className="bg-green-50 rounded-lg p-4">
            <div className="text-sm font-medium text-green-900">Results Returned</div>
            <div className="text-lg font-bold text-green-700 mt-1">
              {metadata.node_count || 0} nodes
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

function getEntitySummary(entities) {
  const types = entities.reduce((acc, entity) => {
    acc[entity.type] = (acc[entity.type] || 0) + 1
    return acc
  }, {})

  return Object.entries(types)
    .map(([type, count]) => `${count} ${type}`)
    .join(', ') || 'None'
}

export default RouterDiagnostics