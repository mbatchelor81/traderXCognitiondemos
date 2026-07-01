import { renderHook, waitFor } from '@testing-library/react';
import React from 'react';
import { GetAccounts } from './GetAccounts';
import { TenantProvider } from '../TenantContext';
import { fetchWithTenant } from '../fetchWithTenant';

jest.mock('../fetchWithTenant', () => ({
  fetchWithTenant: jest.fn(),
}));

const mockedFetch = fetchWithTenant as jest.MockedFunction<typeof fetchWithTenant>;

const wrapper = ({ children }: { children: React.ReactNode }) =>
  React.createElement(TenantProvider, null, children);

describe('GetAccounts', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('returns empty array initially', () => {
    mockedFetch.mockResolvedValue({
      ok: true,
      json: async () => [],
    } as Response);
    const { result } = renderHook(() => GetAccounts(), { wrapper });
    expect(result.current).toEqual([]);
  });

  test('fetches and returns accounts on mount', async () => {
    const mockAccounts = [
      { id: 1, displayName: 'Account One' },
      { id: 2, displayName: 'Account Two' },
    ];
    mockedFetch.mockResolvedValue({
      ok: true,
      json: async () => mockAccounts,
    } as Response);

    const { result } = renderHook(() => GetAccounts(), { wrapper });

    await waitFor(() => {
      expect(result.current).toEqual(mockAccounts);
    });
    expect(mockedFetch).toHaveBeenCalledWith(
      expect.stringContaining('/account/')
    );
  });

  test('handles fetch error gracefully', async () => {
    const consoleSpy = jest.spyOn(console, 'log').mockImplementation();
    mockedFetch.mockResolvedValue({
      ok: false,
      json: async () => ({}),
    } as Response);

    const { result } = renderHook(() => GetAccounts(), { wrapper });

    await waitFor(() => {
      expect(mockedFetch).toHaveBeenCalled();
    });
    expect(result.current).toEqual([]);
    consoleSpy.mockRestore();
  });
});
