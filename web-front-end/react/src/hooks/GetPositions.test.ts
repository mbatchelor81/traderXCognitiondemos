import { renderHook, waitFor } from '@testing-library/react';
import React from 'react';
import { GetPositions } from './GetPositions';
import { TenantProvider } from '../TenantContext';
import { fetchWithTenant } from '../fetchWithTenant';

jest.mock('../fetchWithTenant', () => ({
  fetchWithTenant: jest.fn(),
}));

const mockedFetch = fetchWithTenant as jest.MockedFunction<typeof fetchWithTenant>;

const wrapper = ({ children }: { children: React.ReactNode }) =>
  React.createElement(TenantProvider, null, children);

describe('GetPositions', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('returns empty array when accountId is 0', () => {
    const { result } = renderHook(() => GetPositions(0), { wrapper });
    expect(result.current).toEqual([]);
    expect(mockedFetch).not.toHaveBeenCalled();
  });

  test('fetches positions for a valid accountId', async () => {
    const mockPositions = [
      { accountId: 100, security: 'AAPL', quantity: 500, updated: '2024-01-01' },
      { accountId: 100, security: 'MSFT', quantity: -200, updated: '2024-01-02' },
    ];
    mockedFetch.mockResolvedValue({
      ok: true,
      json: async () => mockPositions,
    } as Response);

    const { result } = renderHook(() => GetPositions(100), { wrapper });

    await waitFor(() => {
      expect(result.current).toEqual(mockPositions);
    });
    expect(mockedFetch).toHaveBeenCalledWith(
      expect.stringContaining('/positions/100'),
      expect.objectContaining({ signal: expect.any(AbortSignal) })
    );
  });

  test('handles fetch error gracefully', async () => {
    mockedFetch.mockRejectedValue(new Error('Network error'));

    const { result } = renderHook(() => GetPositions(200), { wrapper });

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

    const { result } = renderHook(() => GetPositions(300), { wrapper });

    await waitFor(() => {
      expect(mockedFetch).toHaveBeenCalled();
    });
    expect(result.current).toEqual([]);
  });
});
