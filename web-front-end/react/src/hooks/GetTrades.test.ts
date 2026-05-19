import { renderHook, waitFor } from '@testing-library/react';
import React from 'react';
import { GetTrades } from './GetTrades';
import { TenantProvider } from '../TenantContext';
import { fetchWithTenant } from '../fetchWithTenant';

jest.mock('../fetchWithTenant', () => ({
  fetchWithTenant: jest.fn(),
}));

const mockedFetch = fetchWithTenant as jest.MockedFunction<typeof fetchWithTenant>;

const wrapper = ({ children }: { children: React.ReactNode }) =>
  React.createElement(TenantProvider, null, children);

describe('GetTrades', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('returns empty array when accountId is 0', () => {
    const { result } = renderHook(() => GetTrades(0), { wrapper });
    expect(result.current).toEqual([]);
    expect(mockedFetch).not.toHaveBeenCalled();
  });

  test('fetches trades for a valid accountId', async () => {
    const mockTrades = [
      { security: 'AAPL', quantity: 100, side: 'Buy', state: 'New', updated: '2024-01-01' },
      { security: 'GOOGL', quantity: 50, side: 'Sell', state: 'Settled', updated: '2024-01-02' },
    ];
    mockedFetch.mockResolvedValue({
      ok: true,
      json: async () => mockTrades,
    } as Response);

    const { result } = renderHook(() => GetTrades(123), { wrapper });

    await waitFor(() => {
      expect(result.current).toEqual(mockTrades);
    });
    expect(mockedFetch).toHaveBeenCalledWith(
      expect.stringContaining('/trades/123'),
      expect.objectContaining({ signal: expect.any(AbortSignal) })
    );
  });

  test('handles fetch error gracefully', async () => {
    mockedFetch.mockRejectedValue(new Error('Network error'));

    const { result } = renderHook(() => GetTrades(456), { wrapper });

    await waitFor(() => {
      expect(mockedFetch).toHaveBeenCalled();
    });
    expect(result.current).toEqual([]);
  });

  test('handles non-ok response', async () => {
    mockedFetch.mockResolvedValue({
      ok: false,
      json: async () => ({}),
    } as Response);

    const { result } = renderHook(() => GetTrades(789), { wrapper });

    await waitFor(() => {
      expect(mockedFetch).toHaveBeenCalled();
    });
    expect(result.current).toEqual([]);
  });
});
