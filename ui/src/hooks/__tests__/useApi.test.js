import { renderHook, act, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import useApi from '../useApi';

// Mock fetch globally
global.fetch = vi.fn();

describe('useApi', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    fetch.mockClear();
  });

  it('initializes with correct default state', () => {
    const { result } = renderHook(() => useApi());
    
    expect(result.current.data).toBeNull();
    expect(result.current.loading).toBe(false);
    expect(result.current.error).toBeNull();
    expect(typeof result.current.execute).toBe('function');
  });

  it('handles successful API calls', async () => {
    const mockData = { message: 'Success', data: [1, 2, 3] };
    
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockData
    });

    const { result } = renderHook(() => useApi());
    
    await act(async () => {
      await result.current.execute('/api/test');
    });

    expect(result.current.data).toEqual(mockData);
    expect(result.current.loading).toBe(false);
    expect(result.current.error).toBeNull();
  });

  it('sets loading state during API call', async () => {
    fetch.mockImplementationOnce(() => 
      new Promise(resolve => 
        setTimeout(() => resolve({
          ok: true,
          json: async () => ({ data: 'test' })
        }), 100)
      )
    );

    const { result } = renderHook(() => useApi());
    
    act(() => {
      result.current.execute('/api/test');
    });

    expect(result.current.loading).toBe(true);
    expect(result.current.data).toBeNull();
    expect(result.current.error).toBeNull();

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });
  });

  it('handles API errors with error response', async () => {
    const errorResponse = { error: 'Not found' };
    
    fetch.mockResolvedValueOnce({
      ok: false,
      status: 404,
      json: async () => errorResponse
    });

    const { result } = renderHook(() => useApi());
    
    await act(async () => {
      await result.current.execute('/api/notfound');
    });

    expect(result.current.data).toBeNull();
    expect(result.current.loading).toBe(false);
    expect(result.current.error).toBe('Not found');
  });

  it('handles network errors', async () => {
    fetch.mockRejectedValueOnce(new Error('Network error'));

    const { result } = renderHook(() => useApi());
    
    await act(async () => {
      await result.current.execute('/api/test');
    });

    expect(result.current.data).toBeNull();
    expect(result.current.loading).toBe(false);
    expect(result.current.error).toBe('Network error');
  });

  it('supports POST requests with data', async () => {
    const requestData = { query: 'SPY exposure to Apple' };
    const responseData = { answer: 'SPY has 7% exposure', rows: [] };

    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => responseData
    });

    const { result } = renderHook(() => useApi());
    
    await act(async () => {
      await result.current.execute('/api/ask', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestData)
      });
    });

    expect(fetch).toHaveBeenCalledWith('/api/ask', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(requestData)
    });
    
    expect(result.current.data).toEqual(responseData);
  });

  it('supports custom request options', async () => {
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ data: 'custom' })
    });

    const { result } = renderHook(() => useApi());
    
    await act(async () => {
      await result.current.execute('/api/custom', {
        method: 'PUT',
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': 'Bearer token'
        }
      });
    });

    expect(fetch).toHaveBeenCalledWith('/api/custom', {
      method: 'PUT',
      headers: { 
        'Content-Type': 'application/json',
        'Authorization': 'Bearer token'
      }
    });
  });

  it('resets error state on new successful call', async () => {
    const { result } = renderHook(() => useApi());
    
    // First call fails
    fetch.mockResolvedValueOnce({
      ok: false,
      status: 500,
      json: async () => ({ error: 'Server error' })
    });

    await act(async () => {
      await result.current.execute('/api/error');
    });

    expect(result.current.error).toBe('Server error');

    // Second call succeeds
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ data: 'success' })
    });

    await act(async () => {
      await result.current.execute('/api/success');
    });

    expect(result.current.error).toBeNull();
    expect(result.current.data).toEqual({ data: 'success' });
  });

  it('resets data state on new call', async () => {
    const { result } = renderHook(() => useApi());
    
    // First call
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ data: 'first' })
    });

    await act(async () => {
      await result.current.execute('/api/first');
    });

    expect(result.current.data).toEqual({ data: 'first' });

    // Second call
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ data: 'second' })
    });

    await act(async () => {
      await result.current.execute('/api/second');
    });

    expect(result.current.data).toEqual({ data: 'second' });
  });

  it('handles empty response bodies', async () => {
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => null
    });

    const { result } = renderHook(() => useApi());
    
    await act(async () => {
      await result.current.execute('/api/empty');
    });

    expect(result.current.data).toBeNull();
    expect(result.current.error).toBeNull();
  });

  it('handles malformed JSON responses', async () => {
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => {
        throw new Error('Invalid JSON');
      }
    });

    const { result } = renderHook(() => useApi());
    
    await act(async () => {
      await result.current.execute('/api/malformed');
    });

    expect(result.current.data).toBeNull();
    expect(result.current.error).toBe('Invalid JSON');
  });

  it('handles concurrent requests correctly', async () => {
    const { result } = renderHook(() => useApi());
    
    // Mock two different responses
    fetch
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ data: 'first' })
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ data: 'second' })
      });

    // Start two requests concurrently
    const promise1 = act(async () => {
      await result.current.execute('/api/first');
    });
    
    const promise2 = act(async () => {
      await result.current.execute('/api/second');
    });

    await Promise.all([promise1, promise2]);

    // Should have the result of the last completed request
    expect(result.current.data).toEqual({ data: 'second' });
  });

  it('aborts previous request when new request is made', async () => {
    const { result } = renderHook(() => useApi());
    
    // Mock slow first request
    fetch.mockImplementationOnce(() => 
      new Promise(resolve => 
        setTimeout(() => resolve({
          ok: true,
          json: async () => ({ data: 'slow' })
        }), 200)
      )
    );

    // Mock fast second request  
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ data: 'fast' })
    });

    // Start slow request
    act(() => {
      result.current.execute('/api/slow');
    });

    // Immediately start fast request
    await act(async () => {
      await result.current.execute('/api/fast');
    });

    // Should have result from fast request
    expect(result.current.data).toEqual({ data: 'fast' });
  });

  it('supports query parameters in URL', async () => {
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ nodes: [], edges: [] })
    });

    const { result } = renderHook(() => useApi());
    
    await act(async () => {
      await result.current.execute('/api/graph/subgraph?ticker=SPY&top=10');
    });

    expect(fetch).toHaveBeenCalledWith('/api/graph/subgraph?ticker=SPY&top=10', undefined);
  });

  it('preserves loading state consistency', async () => {
    const { result } = renderHook(() => useApi());
    
    fetch.mockImplementationOnce(() => 
      new Promise(resolve => 
        setTimeout(() => resolve({
          ok: true,
          json: async () => ({ data: 'test' })
        }), 50)
      )
    );

    expect(result.current.loading).toBe(false);

    act(() => {
      result.current.execute('/api/test');
    });

    expect(result.current.loading).toBe(true);

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });
  });
});