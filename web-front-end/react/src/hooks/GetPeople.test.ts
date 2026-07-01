import { renderHook, waitFor } from '@testing-library/react';
import React from 'react';
import { GetPeople } from './GetPeople';
import { TenantProvider } from '../TenantContext';
import { fetchWithTenant } from '../fetchWithTenant';

jest.mock('../fetchWithTenant', () => ({
  fetchWithTenant: jest.fn(),
}));

const mockedFetch = fetchWithTenant as jest.MockedFunction<typeof fetchWithTenant>;

const wrapper = ({ children }: { children: React.ReactNode }) =>
  React.createElement(TenantProvider, null, children);

describe('GetPeople', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('returns empty array initially', () => {
    mockedFetch.mockResolvedValue({
      ok: true,
      json: async () => [],
    } as Response);
    const { result } = renderHook(() => GetPeople(), { wrapper });
    expect(result.current).toEqual([]);
  });

  test('fetches and returns people on mount', async () => {
    const mockPeople = [
      { logonId: 'jsmith', fullName: 'John Smith' },
      { logonId: 'jdoe', fullName: 'Jane Doe' },
    ];
    mockedFetch.mockResolvedValue({
      ok: true,
      json: async () => mockPeople,
    } as Response);

    const { result } = renderHook(() => GetPeople(), { wrapper });

    await waitFor(() => {
      expect(result.current).toEqual(mockPeople);
    });
    expect(mockedFetch).toHaveBeenCalledWith(
      expect.stringContaining('/people/')
    );
  });

  test('handles non-ok response gracefully', async () => {
    mockedFetch.mockResolvedValue({
      ok: false,
      json: async () => ({}),
    } as Response);

    const { result } = renderHook(() => GetPeople(), { wrapper });

    await waitFor(() => {
      expect(mockedFetch).toHaveBeenCalled();
    });
    expect(result.current).toEqual([]);
  });

  test('handles fetch exception gracefully', async () => {
    mockedFetch.mockRejectedValue(new Error('Network error'));

    const { result } = renderHook(() => GetPeople(), { wrapper });

    await waitFor(() => {
      expect(mockedFetch).toHaveBeenCalled();
    });
    expect(result.current).toEqual([]);
  });
});
