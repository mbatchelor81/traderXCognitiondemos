import React from 'react';
import { render, screen } from '@testing-library/react';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import { AccountsDropdown } from './AccountsDropdown';
import { TenantProvider } from '../TenantContext';
import { fetchWithTenant } from '../fetchWithTenant';

jest.mock('../fetchWithTenant', () => ({
  fetchWithTenant: jest.fn(),
}));

const mockedFetch = fetchWithTenant as jest.MockedFunction<typeof fetchWithTenant>;
const theme = createTheme();

const renderComponent = (currentAccount: string = '') => {
  const handleChange = jest.fn();
  return render(
    <ThemeProvider theme={theme}>
      <TenantProvider>
        <AccountsDropdown handleChange={handleChange} currentAccount={currentAccount} />
      </TenantProvider>
    </ThemeProvider>
  );
};

describe('AccountsDropdown', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('renders Select Account label', () => {
    mockedFetch.mockResolvedValue({
      ok: true,
      json: async () => [],
    } as Response);

    renderComponent();
    expect(screen.getAllByText('Select Account').length).toBeGreaterThan(0);
  });

  test('renders account count chip', () => {
    mockedFetch.mockResolvedValue({
      ok: true,
      json: async () => [],
    } as Response);

    renderComponent();
    expect(screen.getByText('0 accounts')).toBeInTheDocument();
  });

  test('fetches accounts on mount', async () => {
    const mockAccounts = [
      { id: 1, displayName: 'Account One' },
      { id: 2, displayName: 'Account Two' },
    ];
    mockedFetch.mockResolvedValue({
      ok: true,
      json: async () => mockAccounts,
    } as Response);

    renderComponent();

    expect(mockedFetch).toHaveBeenCalledWith(
      expect.stringContaining('/account/')
    );
  });

  test('displays correct account count after loading', async () => {
    const mockAccounts = [
      { id: 1, displayName: 'Account One' },
      { id: 2, displayName: 'Account Two' },
      { id: 3, displayName: 'Account Three' },
    ];
    mockedFetch.mockResolvedValue({
      ok: true,
      json: async () => mockAccounts,
    } as Response);

    renderComponent();

    const chip = await screen.findByText('3 accounts');
    expect(chip).toBeInTheDocument();
  });
});
