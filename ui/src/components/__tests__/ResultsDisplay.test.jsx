import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import ResultsDisplay from '../query/ResultsDisplay';

describe('ResultsDisplay', () => {
  const mockResultWithData = {
    answer: 'SPY has a 7.0% allocation to Apple Inc (AAPL), representing 178 million shares worth approximately $32.1 billion.',
    rows: [
      { etf_ticker: 'SPY', company_symbol: 'AAPL', company_name: 'Apple Inc', weight: 0.07, shares: 178000000 },
      { etf_ticker: 'SPY', company_symbol: 'MSFT', company_name: 'Microsoft Corp', weight: 0.065, shares: 165000000 }
    ],
    intent: 'etf_exposure_to_company',
    entities: [
      { type: 'ETF', value: 'SPY', ticker: 'SPY' },
      { type: 'Company', value: 'AAPL', symbol: 'AAPL' }
    ],
    metadata: {
      processing_time_ms: 150,
      cache_hit: false,
      node_count: 2,
      edge_count: 1
    }
  };

  const mockResultWithError = {
    error: 'Unable to process query. Please check your input and try again.',
    rows: [],
    intent: null
  };

  const mockEmptyResult = {
    answer: 'No data found for the requested analysis.',
    rows: [],
    intent: 'etf_exposure_to_company',
    entities: []
  };

  it('renders nothing when no result is provided', () => {
    const { container } = render(<ResultsDisplay result={null} />);
    expect(container.firstChild).toBeNull();
  });

  it('displays error message when result has error', () => {
    render(<ResultsDisplay result={mockResultWithError} />);
    
    expect(screen.getByText(/error/i)).toBeInTheDocument();
    expect(screen.getByText(/unable to process query/i)).toBeInTheDocument();
  });

  it('displays LLM answer prominently', () => {
    render(<ResultsDisplay result={mockResultWithData} />);
    
    const answerSection = screen.getByText(/llm analysis/i).closest('div');
    expect(answerSection).toBeInTheDocument();
    expect(screen.getByText(/spy has a 7\.0% allocation/i)).toBeInTheDocument();
  });

  it('displays data table when rows are present', () => {
    render(<ResultsDisplay result={mockResultWithData} />);
    
    // Check for table headers
    expect(screen.getByText(/etf/i)).toBeInTheDocument();
    expect(screen.getByText(/company/i)).toBeInTheDocument();
    expect(screen.getByText(/weight/i)).toBeInTheDocument();
    
    // Check for data rows
    expect(screen.getByText('SPY')).toBeInTheDocument();
    expect(screen.getByText('Apple Inc')).toBeInTheDocument();
    expect(screen.getByText('AAPL')).toBeInTheDocument();
    expect(screen.getByText('7.00%')).toBeInTheDocument();
    
    expect(screen.getByText('Microsoft Corp')).toBeInTheDocument();
    expect(screen.getByText('MSFT')).toBeInTheDocument();
    expect(screen.getByText('6.50%')).toBeInTheDocument();
  });

  it('displays router diagnostics in collapsible section', () => {
    render(<ResultsDisplay result={mockResultWithData} />);
    
    // Should have diagnostics section
    expect(screen.getByText(/router diagnostics/i)).toBeInTheDocument();
    expect(screen.getByText(/intent:/i)).toBeInTheDocument();
    expect(screen.getByText('etf_exposure_to_company')).toBeInTheDocument();
  });

  it('shows entities in diagnostics', () => {
    render(<ResultsDisplay result={mockResultWithData} />);
    
    // Should show detected entities
    expect(screen.getByText(/grounded entities/i)).toBeInTheDocument();
    expect(screen.getByText('ETF: SPY')).toBeInTheDocument();
    expect(screen.getByText('Company: AAPL')).toBeInTheDocument();
  });

  it('displays metadata information', () => {
    render(<ResultsDisplay result={mockResultWithData} />);
    
    // Should show processing metadata
    expect(screen.getByText(/metadata/i)).toBeInTheDocument();
    expect(screen.getByText(/150ms/i)).toBeInTheDocument();
    expect(screen.getByText(/cache hit/i)).toBeInTheDocument();
  });

  it('handles empty results gracefully', () => {
    render(<ResultsDisplay result={mockEmptyResult} />);
    
    expect(screen.getByText(/no data found/i)).toBeInTheDocument();
    expect(screen.getByText(/no results to display/i)).toBeInTheDocument();
  });

  it('formats weights as percentages', () => {
    render(<ResultsDisplay result={mockResultWithData} />);
    
    expect(screen.getByText('7.00%')).toBeInTheDocument();
    expect(screen.getByText('6.50%')).toBeInTheDocument();
  });

  it('formats large numbers with commas', () => {
    render(<ResultsDisplay result={mockResultWithData} />);
    
    expect(screen.getByText('178,000,000')).toBeInTheDocument();
    expect(screen.getByText('165,000,000')).toBeInTheDocument();
  });

  it('displays different table columns based on data structure', () => {
    const overlapResult = {
      answer: 'SPY and QQQ have significant overlap.',
      rows: [
        { company_symbol: 'AAPL', company_name: 'Apple Inc', spy_weight: 0.07, qqq_weight: 0.08, overlap_weight: 0.075 },
        { company_symbol: 'MSFT', company_name: 'Microsoft Corp', spy_weight: 0.065, qqq_weight: 0.07, overlap_weight: 0.0675 }
      ],
      intent: 'etf_overlap_weighted'
    };

    render(<ResultsDisplay result={overlapResult} />);
    
    // Should adapt table columns to data
    expect(screen.getByText(/spy_weight/i)).toBeInTheDocument();
    expect(screen.getByText(/qqq_weight/i)).toBeInTheDocument();
    expect(screen.getByText(/overlap_weight/i)).toBeInTheDocument();
  });

  it('handles missing metadata gracefully', () => {
    const resultWithoutMetadata = {
      answer: 'Test answer',
      rows: [],
      intent: 'test_intent'
    };

    render(<ResultsDisplay result={resultWithoutMetadata} />);
    
    expect(screen.getByText(/test answer/i)).toBeInTheDocument();
    // Should not crash when metadata is missing
  });

  it('shows cache hit indicator', () => {
    const cachedResult = {
      ...mockResultWithData,
      metadata: { ...mockResultWithData.metadata, cache_hit: true }
    };

    render(<ResultsDisplay result={cachedResult} />);
    
    expect(screen.getByText(/cached/i)).toBeInTheDocument();
  });

  it('handles very long answers by truncating appropriately', () => {
    const longAnswerResult = {
      answer: 'This is a very long answer that should be displayed properly without breaking the layout. '.repeat(10),
      rows: [],
      intent: 'test_intent'
    };

    render(<ResultsDisplay result={longAnswerResult} />);
    
    // Should render without layout issues
    const answerElement = screen.getByText(/this is a very long answer/i);
    expect(answerElement).toBeInTheDocument();
  });

  it('handles special characters in data', () => {
    const specialCharResult = {
      answer: 'Analysis of companies with special characters: AT&T, Johnson & Johnson.',
      rows: [
        { company_symbol: 'T', company_name: 'AT&T Inc.', weight: 0.02 },
        { company_symbol: 'JNJ', company_name: 'Johnson & Johnson', weight: 0.015 }
      ],
      intent: 'etf_exposure_to_company'
    };

    render(<ResultsDisplay result={specialCharResult} />);
    
    expect(screen.getByText('AT&T Inc.')).toBeInTheDocument();
    expect(screen.getByText('Johnson & Johnson')).toBeInTheDocument();
  });
});