// API Configuration
export const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

// ETF Configuration
export const ALLOWED_TICKERS = ['SPY', 'QQQ', 'IWM', 'IJH', 'IVE', 'IVW']

// Graph Configuration
export const GRAPH_LAYOUTS = [
  { value: 'cose-bilkent', label: 'Cose Bilkent (Default)' },
  { value: 'fcose', label: 'FCoSE' },
  { value: 'cola', label: 'Cola' },
  { value: 'grid', label: 'Grid' },
  { value: 'circle', label: 'Circle' },
  { value: 'concentric', label: 'Concentric' }
]

export const DEFAULT_GRAPH_LAYOUT = 'cose-bilkent'

// Node Types and Colors
export const NODE_TYPES = {
  ETF: {
    color: '#3B82F6',
    lightColor: '#60A5FA',
    darkColor: '#1D4ED8',
    label: 'ETF'
  },
  Company: {
    color: '#10B981',
    lightColor: '#34D399',
    darkColor: '#047857',
    label: 'Company'
  },
  Sector: {
    color: '#F59E0B',
    lightColor: '#FBBF24',
    darkColor: '#D97706',
    label: 'Sector'
  }
}

// Graph Visualization Settings
export const GRAPH_SETTINGS = {
  minZoom: 0.1,
  maxZoom: 10,
  defaultZoom: 1,
  animationDuration: 500,
  nodeSize: {
    ETF: { width: 60, height: 60 },
    Company: { width: 40, height: 40 },
    Sector: { width: 80, height: 30 }
  },
  edgeWidthRange: { min: 1, max: 8 },
  fontSize: {
    ETF: 12,
    Company: 10,
    Sector: 8
  }
}

// Query Examples
export const EXAMPLE_QUERIES = [
  {
    text: "What is SPY's exposure to AAPL?",
    description: "Find how much SPY holds of Apple"
  },
  {
    text: "Show the overlap between QQQ and SPY",
    description: "Compare holdings between two ETFs"
  },
  {
    text: "What is the sector breakdown for QQQ?",
    description: "See sector allocation within an ETF"
  },
  {
    text: "Which ETFs have at least 20% exposure to Technology?",
    description: "Find ETFs with significant tech exposure"
  },
  {
    text: "Show top 15 holdings in IWM",
    description: "View largest holdings for visualization"
  },
  {
    text: "Which ETFs hold MSFT?",
    description: "Find all ETFs that own Microsoft"
  }
]

// Intent Types
export const INTENT_TYPES = {
  etf_exposure_to_company: 'ETF Exposure to Company',
  etf_overlap_weighted: 'Weighted ETF Overlap',
  etf_overlap_jaccard: 'Jaccard ETF Overlap',
  sector_exposure: 'Sector Exposure',
  etfs_by_sector_threshold: 'ETFs by Sector Threshold',
  top_holdings_subgraph: 'Top Holdings Graph',
  company_rankings: 'Company Rankings'
}

// UI Settings
export const UI_SETTINGS = {
  maxQueryLength: 512,
  defaultTopN: 10,
  maxTopN: 50,
  minTopN: 1,
  defaultEdgeThreshold: 0.0,
  maxEdgeThreshold: 1.0,
  minEdgeThreshold: 0.0,
  debounceDelay: 300,
  animationDuration: 200
}

// Table Settings
export const TABLE_SETTINGS = {
  defaultPageSize: 10,
  pageSizeOptions: [5, 10, 20, 50],
  maxRowsDisplay: 100
}

// Cache Settings
export const CACHE_SETTINGS = {
  queryResultsTTL: 5 * 60 * 1000, // 5 minutes
  graphDataTTL: 10 * 60 * 1000,   // 10 minutes
  userPreferencesTTL: 24 * 60 * 60 * 1000 // 24 hours
}