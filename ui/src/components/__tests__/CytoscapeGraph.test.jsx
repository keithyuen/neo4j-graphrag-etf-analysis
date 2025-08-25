import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import CytoscapeGraph from '../graph/CytoscapeGraph';

// Mock Cytoscape
const mockCytoscape = {
  layout: vi.fn(() => ({
    run: vi.fn(),
    stop: vi.fn()
  })),
  nodes: vi.fn(() => ({
    length: 3
  })),
  edges: vi.fn(() => ({
    length: 2
  })),
  fit: vi.fn(),
  center: vi.fn(),
  on: vi.fn(),
  off: vi.fn(),
  destroy: vi.fn(),
  add: vi.fn(),
  remove: vi.fn(),
  style: vi.fn(),
  resize: vi.fn()
};

vi.mock('cytoscape', () => ({
  default: vi.fn(() => mockCytoscape)
}));

// Mock fetch
global.fetch = vi.fn();

describe('CytoscapeGraph', () => {
  const mockGraphData = {
    nodes: [
      { id: 'SPY', label: 'SPY', type: 'ETF', name: 'SPDR S&P 500 ETF' },
      { id: 'AAPL', label: 'AAPL', type: 'Company', name: 'Apple Inc' },
      { id: 'Information Technology', label: 'Information Technology', type: 'Sector' }
    ],
    edges: [
      { source: 'SPY', target: 'AAPL', weight: 0.07, shares: 178000000 },
      { source: 'AAPL', target: 'Information Technology', weight: 1.0 }
    ]
  };

  beforeEach(() => {
    vi.clearAllMocks();
    fetch.mockClear();
    mockCytoscape.layout.mockClear();
    mockCytoscape.fit.mockClear();
  });

  it('renders graph container and controls', () => {
    render(<CytoscapeGraph />);
    
    expect(screen.getByText(/etf subgraph visualization/i)).toBeInTheDocument();
    expect(screen.getByText(/ticker/i)).toBeInTheDocument();
    expect(screen.getByText(/layout/i)).toBeInTheDocument();
    expect(screen.getByText(/top holdings/i)).toBeInTheDocument();
  });

  it('renders ticker selection dropdown', () => {
    render(<CytoscapeGraph />);
    
    const tickerSelect = screen.getByLabelText(/ticker/i);
    expect(tickerSelect).toBeInTheDocument();
    
    // Should have allowed tickers as options
    expect(screen.getByText('SPY')).toBeInTheDocument();
    expect(screen.getByText('QQQ')).toBeInTheDocument();
    expect(screen.getByText('IWM')).toBeInTheDocument();
  });

  it('renders layout selection controls', () => {
    render(<CytoscapeGraph />);
    
    expect(screen.getByText(/cose-bilkent/i)).toBeInTheDocument();
    expect(screen.getByText(/fcose/i)).toBeInTheDocument();
    expect(screen.getByText(/cola/i)).toBeInTheDocument();
  });

  it('renders top holdings slider', () => {
    render(<CytoscapeGraph />);
    
    const slider = screen.getByLabelText(/top holdings/i);
    expect(slider).toBeInTheDocument();
    expect(slider.type).toBe('range');
    expect(slider.min).toBe('5');
    expect(slider.max).toBe('50');
  });

  it('fetches graph data when ticker changes', async () => {
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockGraphData
    });

    render(<CytoscapeGraph />);
    
    const tickerSelect = screen.getByLabelText(/ticker/i);
    fireEvent.change(tickerSelect, { target: { value: 'SPY' } });
    
    await waitFor(() => {
      expect(fetch).toHaveBeenCalledWith('/api/graph/subgraph?ticker=SPY&top=10');
    });
  });

  it('handles API errors gracefully', async () => {
    fetch.mockResolvedValueOnce({
      ok: false,
      status: 404,
      json: async () => ({ error: 'Not found' })
    });

    render(<CytoscapeGraph />);
    
    const tickerSelect = screen.getByLabelText(/ticker/i);
    fireEvent.change(tickerSelect, { target: { value: 'SPY' } });
    
    await waitFor(() => {
      expect(screen.getByText(/error loading graph/i)).toBeInTheDocument();
    });
  });

  it('shows loading state during data fetch', async () => {
    fetch.mockImplementationOnce(() => 
      new Promise(resolve => 
        setTimeout(() => resolve({
          ok: true,
          json: async () => mockGraphData
        }), 100)
      )
    );

    render(<CytoscapeGraph />);
    
    const tickerSelect = screen.getByLabelText(/ticker/i);
    fireEvent.change(tickerSelect, { target: { value: 'SPY' } });
    
    expect(screen.getByText(/loading graph/i)).toBeInTheDocument();
    
    await waitFor(() => {
      expect(screen.queryByText(/loading graph/i)).not.toBeInTheDocument();
    });
  });

  it('updates top holdings parameter when slider changes', async () => {
    fetch.mockResolvedValue({
      ok: true,
      json: async () => mockGraphData
    });

    render(<CytoscapeGraph />);
    
    // First select a ticker
    const tickerSelect = screen.getByLabelText(/ticker/i);
    fireEvent.change(tickerSelect, { target: { value: 'SPY' } });
    
    await waitFor(() => {
      expect(fetch).toHaveBeenCalledWith('/api/graph/subgraph?ticker=SPY&top=10');
    });

    // Then change the slider
    const slider = screen.getByLabelText(/top holdings/i);
    fireEvent.change(slider, { target: { value: '20' } });
    
    await waitFor(() => {
      expect(fetch).toHaveBeenCalledWith('/api/graph/subgraph?ticker=SPY&top=20');
    });
  });

  it('changes layout when layout option is selected', async () => {
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockGraphData
    });

    render(<CytoscapeGraph />);
    
    // Load some data first
    const tickerSelect = screen.getByLabelText(/ticker/i);
    fireEvent.change(tickerSelect, { target: { value: 'SPY' } });
    
    await waitFor(() => {
      expect(fetch).toHaveBeenCalled();
    });

    // Change layout
    const fcoseButton = screen.getByText(/fcose/i);
    fireEvent.click(fcoseButton);
    
    // Should trigger layout change
    expect(mockCytoscape.layout).toHaveBeenCalledWith(
      expect.objectContaining({ name: 'fcose' })
    );
  });

  it('displays graph legend', () => {
    render(<CytoscapeGraph />);
    
    expect(screen.getByText(/legend/i)).toBeInTheDocument();
    expect(screen.getByText(/etf/i)).toBeInTheDocument();
    expect(screen.getByText(/company/i)).toBeInTheDocument();
    expect(screen.getByText(/sector/i)).toBeInTheDocument();
  });

  it('shows node and edge counts', async () => {
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockGraphData
    });

    render(<CytoscapeGraph />);
    
    const tickerSelect = screen.getByLabelText(/ticker/i);
    fireEvent.change(tickerSelect, { target: { value: 'SPY' } });
    
    await waitFor(() => {
      expect(screen.getByText(/3 nodes/i)).toBeInTheDocument();
      expect(screen.getByText(/2 edges/i)).toBeInTheDocument();
    });
  });

  it('handles empty graph data', async () => {
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ nodes: [], edges: [] })
    });

    render(<CytoscapeGraph />);
    
    const tickerSelect = screen.getByLabelText(/ticker/i);
    fireEvent.change(tickerSelect, { target: { value: 'SPY' } });
    
    await waitFor(() => {
      expect(screen.getByText(/no graph data/i)).toBeInTheDocument();
    });
  });

  it('applies edge weight threshold filter', async () => {
    fetch.mockResolvedValue({
      ok: true,
      json: async () => mockGraphData
    });

    render(<CytoscapeGraph />);
    
    // Load data first
    const tickerSelect = screen.getByLabelText(/ticker/i);
    fireEvent.change(tickerSelect, { target: { value: 'SPY' } });
    
    await waitFor(() => {
      expect(fetch).toHaveBeenCalled();
    });

    // Change edge threshold
    const thresholdSlider = screen.getByLabelText(/edge weight threshold/i);
    fireEvent.change(thresholdSlider, { target: { value: '0.05' } });
    
    // Should update graph filtering
    expect(mockCytoscape.style).toHaveBeenCalled();
  });

  it('handles window resize events', async () => {
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockGraphData
    });

    render(<CytoscapeGraph />);
    
    // Load data
    const tickerSelect = screen.getByLabelText(/ticker/i);
    fireEvent.change(tickerSelect, { target: { value: 'SPY' } });
    
    await waitFor(() => {
      expect(fetch).toHaveBeenCalled();
    });

    // Simulate window resize
    fireEvent.resize(window);
    
    // Should call resize on cytoscape
    expect(mockCytoscape.resize).toHaveBeenCalled();
  });

  it('cleans up cytoscape instance on unmount', async () => {
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockGraphData
    });

    const { unmount } = render(<CytoscapeGraph />);
    
    // Load data to create cytoscape instance
    const tickerSelect = screen.getByLabelText(/ticker/i);
    fireEvent.change(tickerSelect, { target: { value: 'SPY' } });
    
    await waitFor(() => {
      expect(fetch).toHaveBeenCalled();
    });

    // Unmount component
    unmount();
    
    // Should destroy cytoscape instance
    expect(mockCytoscape.destroy).toHaveBeenCalled();
  });

  it('displays tooltips on node hover', async () => {
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockGraphData
    });

    render(<CytoscapeGraph />);
    
    const tickerSelect = screen.getByLabelText(/ticker/i);
    fireEvent.change(tickerSelect, { target: { value: 'SPY' } });
    
    await waitFor(() => {
      expect(fetch).toHaveBeenCalled();
    });

    // Should have set up event listeners for tooltips
    expect(mockCytoscape.on).toHaveBeenCalledWith('mouseover', 'node', expect.any(Function));
    expect(mockCytoscape.on).toHaveBeenCalledWith('mouseout', 'node', expect.any(Function));
  });

  it('fits graph to container after layout', async () => {
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockGraphData
    });

    render(<CytoscapeGraph />);
    
    const tickerSelect = screen.getByLabelText(/ticker/i);
    fireEvent.change(tickerSelect, { target: { value: 'SPY' } });
    
    await waitFor(() => {
      expect(fetch).toHaveBeenCalled();
    });

    // Should fit graph to container
    expect(mockCytoscape.fit).toHaveBeenCalled();
  });
});