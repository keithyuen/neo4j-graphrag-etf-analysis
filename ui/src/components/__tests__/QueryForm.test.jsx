import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import QueryForm from '../query/QueryForm';

// Mock fetch globally
global.fetch = vi.fn();

describe('QueryForm', () => {
  const mockOnResult = vi.fn();
  const mockOnLoading = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    fetch.mockClear();
  });

  it('renders query form with input and button', () => {
    render(<QueryForm onResult={mockOnResult} onLoading={mockOnLoading} />);
    
    expect(screen.getByPlaceholderText(/ask about etf/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /analyze/i })).toBeInTheDocument();
  });

  it('handles input changes correctly', () => {
    render(<QueryForm onResult={mockOnResult} onLoading={mockOnLoading} />);
    
    const input = screen.getByPlaceholderText(/ask about etf/i);
    fireEvent.change(input, { target: { value: 'SPY exposure to Apple' } });
    
    expect(input.value).toBe('SPY exposure to Apple');
  });

  it('disables button when input is empty', () => {
    render(<QueryForm onResult={mockOnResult} onLoading={mockOnLoading} />);
    
    const button = screen.getByRole('button', { name: /analyze/i });
    expect(button).toBeDisabled();
  });

  it('enables button when input has content', () => {
    render(<QueryForm onResult={mockOnResult} onLoading={mockOnLoading} />);
    
    const input = screen.getByPlaceholderText(/ask about etf/i);
    const button = screen.getByRole('button', { name: /analyze/i });
    
    fireEvent.change(input, { target: { value: 'SPY exposure to Apple' } });
    
    expect(button).not.toBeDisabled();
  });

  it('calls onLoading when form is submitted', async () => {
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        answer: 'SPY has 7% exposure to Apple',
        rows: [],
        intent: 'etf_exposure_to_company'
      })
    });

    render(<QueryForm onResult={mockOnResult} onLoading={mockOnLoading} />);
    
    const input = screen.getByPlaceholderText(/ask about etf/i);
    const button = screen.getByRole('button', { name: /analyze/i });
    
    fireEvent.change(input, { target: { value: 'SPY exposure to Apple' } });
    fireEvent.click(button);
    
    expect(mockOnLoading).toHaveBeenCalledWith(true);
  });

  it('submits query and calls onResult with response', async () => {
    const mockResponse = {
      answer: 'SPY has 7% exposure to Apple Inc (AAPL).',
      rows: [{ etf_ticker: 'SPY', company_symbol: 'AAPL', weight: 0.07 }],
      intent: 'etf_exposure_to_company',
      entities: [
        { type: 'ETF', value: 'SPY' },
        { type: 'Company', value: 'AAPL' }
      ]
    };

    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockResponse
    });

    render(<QueryForm onResult={mockOnResult} onLoading={mockOnLoading} />);
    
    const input = screen.getByPlaceholderText(/ask about etf/i);
    const button = screen.getByRole('button', { name: /analyze/i });
    
    fireEvent.change(input, { target: { value: 'SPY exposure to Apple' } });
    fireEvent.click(button);
    
    await waitFor(() => {
      expect(mockOnResult).toHaveBeenCalledWith(mockResponse);
      expect(mockOnLoading).toHaveBeenCalledWith(false);
    });
  });

  it('handles API errors gracefully', async () => {
    fetch.mockResolvedValueOnce({
      ok: false,
      status: 400,
      json: async () => ({ error: 'Invalid query' })
    });

    render(<QueryForm onResult={mockOnResult} onLoading={mockOnLoading} />);
    
    const input = screen.getByPlaceholderText(/ask about etf/i);
    const button = screen.getByRole('button', { name: /analyze/i });
    
    fireEvent.change(input, { target: { value: 'invalid query' } });
    fireEvent.click(button);
    
    await waitFor(() => {
      expect(mockOnLoading).toHaveBeenCalledWith(false);
      expect(mockOnResult).toHaveBeenCalledWith(
        expect.objectContaining({ error: expect.any(String) })
      );
    });
  });

  it('handles network errors', async () => {
    fetch.mockRejectedValueOnce(new Error('Network error'));

    render(<QueryForm onResult={mockOnResult} onLoading={mockOnLoading} />);
    
    const input = screen.getByPlaceholderText(/ask about etf/i);
    const button = screen.getByRole('button', { name: /analyze/i });
    
    fireEvent.change(input, { target: { value: 'SPY exposure to Apple' } });
    fireEvent.click(button);
    
    await waitFor(() => {
      expect(mockOnLoading).toHaveBeenCalledWith(false);
      expect(mockOnResult).toHaveBeenCalledWith(
        expect.objectContaining({ error: expect.stringContaining('Network') })
      );
    });
  });

  it('shows loading state during submission', async () => {
    // Simulate slow network
    fetch.mockImplementationOnce(() => 
      new Promise(resolve => 
        setTimeout(() => resolve({
          ok: true,
          json: async () => ({ answer: 'Response', rows: [] })
        }), 100)
      )
    );

    render(<QueryForm onResult={mockOnResult} onLoading={mockOnLoading} />);
    
    const input = screen.getByPlaceholderText(/ask about etf/i);
    const button = screen.getByRole('button', { name: /analyze/i });
    
    fireEvent.change(input, { target: { value: 'SPY exposure to Apple' } });
    fireEvent.click(button);
    
    // Should show loading state
    expect(screen.getByText(/analyzing/i)).toBeInTheDocument();
    expect(button).toBeDisabled();
    
    await waitFor(() => {
      expect(mockOnLoading).toHaveBeenCalledWith(false);
    });
  });

  it('supports Enter key submission', async () => {
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ answer: 'Response', rows: [] })
    });

    render(<QueryForm onResult={mockOnResult} onLoading={mockOnLoading} />);
    
    const input = screen.getByPlaceholderText(/ask about etf/i);
    
    fireEvent.change(input, { target: { value: 'SPY exposure to Apple' } });
    fireEvent.keyPress(input, { key: 'Enter', code: 'Enter', charCode: 13 });
    
    await waitFor(() => {
      expect(fetch).toHaveBeenCalledWith('/api/ask', expect.objectContaining({
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: 'SPY exposure to Apple' })
      }));
    });
  });

  it('prevents double submission', async () => {
    fetch.mockImplementationOnce(() => 
      new Promise(resolve => 
        setTimeout(() => resolve({
          ok: true,
          json: async () => ({ answer: 'Response', rows: [] })
        }), 100)
      )
    );

    render(<QueryForm onResult={mockOnResult} onLoading={mockOnLoading} />);
    
    const input = screen.getByPlaceholderText(/ask about etf/i);
    const button = screen.getByRole('button', { name: /analyze/i });
    
    fireEvent.change(input, { target: { value: 'SPY exposure to Apple' } });
    
    // Click multiple times quickly
    fireEvent.click(button);
    fireEvent.click(button);
    fireEvent.click(button);
    
    // Should only make one API call
    await waitFor(() => {
      expect(fetch).toHaveBeenCalledTimes(1);
    });
  });
});