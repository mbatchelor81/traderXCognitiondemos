import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import { CreateTradeButton } from './CreateTradeButton';
import { fetchWithTenant } from '../fetchWithTenant';

jest.mock('../fetchWithTenant', () => ({
  fetchWithTenant: jest.fn(),
}));

const mockedFetch = fetchWithTenant as jest.MockedFunction<typeof fetchWithTenant>;
const theme = createTheme();

const renderComponent = (accountId: number = 123) =>
  render(
    <ThemeProvider theme={theme}>
      <CreateTradeButton accountId={accountId} />
    </ThemeProvider>
  );

describe('CreateTradeButton', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('renders the New Trade button', () => {
    renderComponent();
    expect(screen.getByText('New Trade')).toBeInTheDocument();
  });

  test('button is disabled when accountId is 0', () => {
    renderComponent(0);
    expect(screen.getByText('New Trade').closest('button')).toBeDisabled();
  });

  test('button is enabled when accountId is provided', () => {
    renderComponent(123);
    expect(screen.getByText('New Trade').closest('button')).not.toBeDisabled();
  });

  test('opens dialog and loads stocks on button click', async () => {
    const mockStocks = [
      { ticker: 'AAPL', companyName: 'Apple Inc' },
      { ticker: 'GOOGL', companyName: 'Alphabet Inc' },
    ];
    mockedFetch.mockResolvedValue({
      ok: true,
      json: async () => mockStocks,
    } as Response);

    renderComponent();
    await userEvent.click(screen.getByText('New Trade'));

    expect(screen.getByText('Create Trade')).toBeInTheDocument();
    await waitFor(() => {
      expect(mockedFetch).toHaveBeenCalledWith(
        expect.stringContaining('/stocks')
      );
    });
  });

  test('shows loading spinner while fetching stocks', async () => {
    mockedFetch.mockImplementation(
      () => new Promise((resolve) => setTimeout(() => resolve({ ok: true, json: async () => [] } as Response), 100))
    );

    renderComponent();
    await userEvent.click(screen.getByText('New Trade'));
    expect(screen.getByRole('progressbar')).toBeInTheDocument();
  });

  test('displays Buy and Sell toggle buttons in dialog', async () => {
    mockedFetch.mockResolvedValue({
      ok: true,
      json: async () => [],
    } as Response);

    renderComponent();
    await userEvent.click(screen.getByText('New Trade'));

    await waitFor(() => {
      expect(screen.getByText('Buy')).toBeInTheDocument();
      expect(screen.getByText('Sell')).toBeInTheDocument();
    });
  });

  test('closes dialog when close button is clicked', async () => {
    mockedFetch.mockResolvedValue({
      ok: true,
      json: async () => [],
    } as Response);

    renderComponent();
    await userEvent.click(screen.getByText('New Trade'));
    expect(screen.getByText('Create Trade')).toBeInTheDocument();

    await userEvent.click(screen.getByText('Cancel'));
    await waitFor(() => {
      expect(screen.queryByText('Create Trade')).not.toBeInTheDocument();
    });
  });
});
