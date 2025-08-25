import { Bot, Copy, Check, AlertCircle } from 'lucide-react'
import { useState } from 'react'
import clsx from 'clsx'

function LLMAnswer({ answer, metadata, className = '' }) {
  const [copied, setCopied] = useState(false)

  if (!answer) {
    return null
  }

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(answer)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch (error) {
      console.error('Failed to copy text:', error)
    }
  }

  const isErrorAnswer = answer.toLowerCase().includes('no results found') || 
                       answer.toLowerCase().includes('error') ||
                       answer.toLowerCase().includes('failed')

  const confidence = metadata?.confidence || 0
  const isLowConfidence = confidence < 0.7

  return (
    <div className={clsx('card animate-fade-in', className)}>
      <div className="card-header border-b-2 border-primary-100">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <div className="w-8 h-8 bg-primary-100 rounded-lg flex items-center justify-center">
              <Bot className="w-5 h-5 text-primary-600" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-gray-900">AI Analysis</h3>
              <p className="text-xs text-gray-500">
                Generated with GraphRAG pipeline
              </p>
            </div>
          </div>
          
          <div className="flex items-center space-x-2">
            {isLowConfidence && (
              <div className="flex items-center space-x-1 text-amber-600">
                <AlertCircle className="w-4 h-4" />
                <span className="text-xs">Low confidence</span>
              </div>
            )}
            
            <button
              onClick={handleCopy}
              className="btn-outline !p-2"
              title="Copy answer"
            >
              {copied ? (
                <Check className="w-4 h-4 text-green-600" />
              ) : (
                <Copy className="w-4 h-4" />
              )}
            </button>
          </div>
        </div>
      </div>

      <div className="card-body">
        <div className={clsx(
          'prose prose-sm max-w-none',
          isErrorAnswer ? 'text-red-700' : 'text-gray-800'
        )}>
          <p className="text-base leading-relaxed whitespace-pre-wrap">
            {answer}
          </p>
        </div>

        {/* Metadata */}
        {metadata && (
          <div className="mt-4 pt-4 border-t border-gray-100">
            <div className="flex flex-wrap items-center gap-4 text-xs text-gray-500">
              {metadata.confidence !== undefined && (
                <div className="flex items-center space-x-1">
                  <span>Confidence:</span>
                  <span className={clsx(
                    'font-medium',
                    metadata.confidence >= 0.8 ? 'text-green-600' :
                    metadata.confidence >= 0.6 ? 'text-yellow-600' : 'text-red-600'
                  )}>
                    {Math.round(metadata.confidence * 100)}%
                  </span>
                </div>
              )}
              
              {metadata.timing?.total_pipeline && (
                <div className="flex items-center space-x-1">
                  <span>Query time:</span>
                  <span className="font-medium">
                    {metadata.timing.total_pipeline >= 1000 
                      ? `${(metadata.timing.total_pipeline / 1000).toFixed(2)}s` 
                      : `${Math.round(metadata.timing.total_pipeline)}ms`}
                  </span>
                </div>
              )}
              
              {metadata.node_count !== undefined && (
                <div className="flex items-center space-x-1">
                  <span>Nodes analyzed:</span>
                  <span className="font-medium">{metadata.node_count}</span>
                </div>
              )}
              
              {metadata.cache_hit !== undefined && (
                <div className="flex items-center space-x-1">
                  <span>Cache:</span>
                  <span className={clsx(
                    'font-medium',
                    metadata.cache_hit ? 'text-green-600' : 'text-blue-600'
                  )}>
                    {metadata.cache_hit ? 'Hit' : 'Miss'}
                  </span>
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Warning for low confidence */}
      {isLowConfidence && (
        <div className="mx-6 mb-4 p-3 bg-amber-50 border border-amber-200 rounded-lg">
          <div className="flex items-start space-x-2">
            <AlertCircle className="w-4 h-4 text-amber-600 mt-0.5 flex-shrink-0" />
            <div className="text-sm text-amber-800">
              <div className="font-medium">Low Confidence Result</div>
              <div className="text-xs mt-1">
                The system has low confidence in this answer. Consider rephrasing your query or providing more specific details.
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default LLMAnswer