import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { BrowserRouter } from 'react-router-dom';
import Home from '../Home';

// Mock child components
vi.mock('../../components/query/QueryForm', () => ({
  default: ({ onResult, onLoading }) => (
    <div data-testid="query-form">
      <button 
        onClick={() => {
          onLoading(true);
          setTimeout(() => {
            onResult({
              answer: 'Mock answer',
              rows: [{ test: 'data' }],
              intent: 'mock_intent'
            });
            onLoading(false);
          }, 100);
        }}
      >
        Submit Query
      </button>
    </div>
  )
}));

vi.mock('../../components/query/ResultsDisplay', () => ({
  default: ({ result }) => (
    <div data-testid="results-display">
      {result && <div>{result.answer}</div>}
    </div>
  )
}));

vi.mock('../../components/common/LoadingSpinner', () => ({
  default: () => <div data-testid="loading-spinner">Loading...</div>
}));

// Mock fetch for ETL refresh
global.fetch = vi.fn();

const HomeWithRouter = () => (
  <BrowserRouter>
    <Home />
  </BrowserRouter>
);

describe('Home', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    fetch.mockClear();
  });

  it('renders page title and description', () => {
    render(<HomeWithRouter />);
    
    expect(screen.getByText(/etf composition & overlap analysis/i)).toBeInTheDocument();
    expect(screen.getByText(/analyze etf holdings/i)).toBeInTheDocument();
  });

  it('renders query form', () => {
    render(<HomeWithRouter />);
    
    expect(screen.getByTestId('query-form')).toBeInTheDocument();
  });

  it('renders ETL refresh controls', () => {
    render(<HomeWithRouter />);
    
    expect(screen.getByText(/data management/i)).toBeInTheDocument();
    expect(screen.getByText(/refresh etf data/i)).toBeInTheDocument();
    expect(screen.getByText(/force refresh/i)).toBeInTheDocument();
  });

  it('shows loading spinner when query is processing', async () => {
    render(<HomeWithRouter />);
    
    const submitButton = screen.getByText('Submit Query');
    fireEvent.click(submitButton);
    
    expect(screen.getByTestId('loading-spinner')).toBeInTheDocument();
    
    await waitFor(() => {
      expect(screen.queryByTestId('loading-spinner')).not.toBeInTheDocument();
    });
  });

  it('displays results after query completion', async () => {
    render(<HomeWithRouter />);
    
    const submitButton = screen.getByText('Submit Query');
    fireEvent.click(submitButton);
    
    await waitFor(() => {
      expect(screen.getByTestId('results-display')).toBeInTheDocument();
      expect(screen.getByText('Mock answer')).toBeInTheDocument();
    });
  });

  it('handles ETL refresh button click', async () => {
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        updated_etfs: ['SPY', 'QQQ'],
        total_holdings: 1000,
        cache_status: 'refreshed'
      })
    });

    render(<HomeWithRouter />);
    
    const refreshButton = screen.getByText(/refresh etf data/i);
    fireEvent.click(refreshButton);
    
    await waitFor(() => {
      expect(fetch).toHaveBeenCalledWith('/api/etl/refresh', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ tickers: ['SPY', 'QQQ', 'IWM', 'IJH', 'IVE', 'IVW'] })
      });
    });
  });

  it('handles force refresh button click', async () => {
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        updated_etfs: ['SPY', 'QQQ', 'IWM', 'IJH', 'IVE', 'IVW'],
        total_holdings: 3000,
        cache_status: 'force_refreshed'
      })
    });

    render(<HomeWithRouter />);
    
    const forceRefreshButton = screen.getByText(/force refresh/i);
    fireEvent.click(forceRefreshButton);
    
    await waitFor(() => {
      expect(fetch).toHaveBeenCalledWith('/api/etl/refresh/force', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });
    });
  });

  it('shows ETL refresh success message', async () => {
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        updated_etfs: ['SPY', 'QQQ'],
        total_holdings: 1000,
        cache_status: 'refreshed'
      })
    });

    render(<HomeWithRouter />);
    
    const refreshButton = screen.getByText(/refresh etf data/i);
    fireEvent.click(refreshButton);
    
    await waitFor(() => {
      expect(screen.getByText(/data refreshed successfully/i)).toBeInTheDocument();
      expect(screen.getByText(/updated 2 etfs/i)).toBeInTheDocument();
    });
  });

  it('shows ETL refresh error message', async () => {
    fetch.mockResolvedValueOnce({
      ok: false,
      status: 500,
      json: async () => ({ error: 'Server error' })
    });

    render(<HomeWithRouter />);
    
    const refreshButton = screen.getByText(/refresh etf data/i);
    fireEvent.click(refreshButton);
    
    await waitFor(() => {
      expect(screen.getByText(/error refreshing data/i)).toBeInTheDocument();
    });
  });

  it('disables ETL buttons during refresh', async () => {
    fetch.mockImplementationOnce(() => 
      new Promise(resolve => 
        setTimeout(() => resolve({
          ok: true,
          json: async () => ({ updated_etfs: [], total_holdings: 0 })
        }), 100)
      )
    );

    render(<HomeWithRouter />);
    
    const refreshButton = screen.getByText(/refresh etf data/i);
    const forceRefreshButton = screen.getByText(/force refresh/i);
    
    fireEvent.click(refreshButton);
    
    expect(refreshButton).toBeDisabled();
    expect(forceRefreshButton).toBeDisabled();
    
    await waitFor(() => {
      expect(refreshButton).not.toBeDisabled();
      expect(forceRefreshButton).not.toBeDisabled();
    });
  });

  it('handles network errors during ETL refresh', async () => {
    fetch.mockRejectedValueOnce(new Error('Network error'));

    render(<HomeWithRouter />);
    
    const refreshButton = screen.getByText(/refresh etf data/i);
    fireEvent.click(refreshButton);
    
    await waitFor(() => {
      expect(screen.getByText(/network error/i)).toBeInTheDocument();
    });
  });

  it('links to graph page', () => {
    render(<HomeWithRouter />);
    
    const graphLink = screen.getByText(/view interactive graph/i);
    expect(graphLink).toBeInTheDocument();
    expect(graphLink.closest('a')).toHaveAttribute('href', '/graph');
  });

  it('shows sample queries section', () => {
    render(<HomeWithRouter />);
    
    expect(screen.getByText(/sample queries/i)).toBeInTheDocument();
    expect(screen.getByText(/spy exposure to apple/i)).toBeInTheDocument();
    expect(screen.getByText(/qqq vs iwm overlap/i)).toBeInTheDocument();
    expect(screen.getByText(/technology sector allocation/i)).toBeInTheDocument();
  });

  it('handles sample query clicks', async () => {
    const mockQueryForm = vi.fn();
    
    // Mock the QueryForm to capture props
    vi.doMock('../../components/query/QueryForm', () => ({
      default: (props) => {
        mockQueryForm(props);
        return <div data-testid="query-form">Query Form</div>;
      }
    }));

    render(<HomeWithRouter />);
    
    const sampleQuery = screen.getByText(/spy exposure to apple/i);
    fireEvent.click(sampleQuery);
    
    // Should trigger query form with sample query
    expect(mockQueryForm).toHaveBeenCalled();
  });

  it('displays cache status information', async () => {
    // Mock cache stats endpoint
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        total_entries: 150,
        hit_rate: 0.75,
        memory_usage_mb: 45.2
      })
    });

    render(<HomeWithRouter />);
    
    // Should fetch and display cache stats
    await waitFor(() => {
      expect(fetch).toHaveBeenCalledWith('/api/cache/stats');
    });
  });

  it('shows system status indicators', () => {
    render(<HomeWithRouter />);
    
    // Should show system status
    expect(screen.getByText(/system status/i)).toBeInTheDocument();
  });

  it('handles concurrent operations gracefully', async () => {
    fetch
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ updated_etfs: [], total_holdings: 0 })
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ updated_etfs: [], total_holdings: 0 })
      });

    render(<HomeWithRouter />);
    
    const refreshButton = screen.getByText(/refresh etf data/i);
    const submitButton = screen.getByText('Submit Query');
    
    // Click both buttons rapidly
    fireEvent.click(refreshButton);
    fireEvent.click(submitButton);
    
    // Should handle both operations
    await waitFor(() => {
      expect(fetch).toHaveBeenCalledTimes(2);
    });
  });

  it('preserves query results during ETL operations', async () => {
    fetch.mockResolvedValue({
      ok: true,
      json: async () => ({ updated_etfs: [], total_holdings: 0 })
    });

    render(<HomeWithRouter />);
    
    // Submit a query first
    const submitButton = screen.getByText('Submit Query');
    fireEvent.click(submitButton);
    
    await waitFor(() => {
      expect(screen.getByText('Mock answer')).toBeInTheDocument();
    });
    
    // Then do ETL refresh
    const refreshButton = screen.getByText(/refresh etf data/i);
    fireEvent.click(refreshButton);
    
    await waitFor(() => {
      expect(fetch).toHaveBeenCalled();
    });
    
    // Results should still be visible
    expect(screen.getByText('Mock answer')).toBeInTheDocument();
  });
});