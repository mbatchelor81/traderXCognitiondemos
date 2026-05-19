import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import { CreateAccount } from './CreateAccount';
import { fetchWithTenant } from '../fetchWithTenant';

jest.mock('../fetchWithTenant', () => ({
  fetchWithTenant: jest.fn(),
}));

const mockedFetch = fetchWithTenant as jest.MockedFunction<typeof fetchWithTenant>;
const theme = createTheme();

const renderComponent = () =>
  render(
    <ThemeProvider theme={theme}>
      <CreateAccount />
    </ThemeProvider>
  );

describe('CreateAccount', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('renders the New Account button', () => {
    renderComponent();
    expect(screen.getByText('New Account')).toBeInTheDocument();
  });

  test('opens dialog when button is clicked', async () => {
    renderComponent();
    await userEvent.click(screen.getByText('New Account'));
    expect(screen.getByText('Create Account')).toBeInTheDocument();
    expect(screen.getByLabelText('Display Name')).toBeInTheDocument();
  });

  test('shows error when submitting with empty name', async () => {
    renderComponent();
    await userEvent.click(screen.getByText('New Account'));
    // Type a space and clear it to trigger validation via Enter key
    const input = screen.getByLabelText('Display Name');
    await userEvent.type(input, ' ');
    await userEvent.clear(input);
    await userEvent.keyboard('{Enter}');
    expect(screen.getByText('Display name is required')).toBeInTheDocument();
  });

  test('submits successfully with valid display name', async () => {
    mockedFetch.mockResolvedValue({
      ok: true,
      json: async () => ({}),
    } as Response);

    renderComponent();
    await userEvent.click(screen.getByText('New Account'));
    await userEvent.type(screen.getByLabelText('Display Name'), 'Test Account');
    await userEvent.click(screen.getByText('Create'));

    await waitFor(() => {
      expect(mockedFetch).toHaveBeenCalledWith(
        expect.stringContaining('/account/'),
        expect.objectContaining({
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: expect.stringContaining('Test Account'),
        })
      );
    });
  });

  test('shows error snackbar on failed submission', async () => {
    mockedFetch.mockResolvedValue({
      ok: false,
      json: async () => ({}),
    } as Response);

    renderComponent();
    await userEvent.click(screen.getByText('New Account'));
    await userEvent.type(screen.getByLabelText('Display Name'), 'Test Account');
    await userEvent.click(screen.getByText('Create'));

    await waitFor(() => {
      expect(screen.getByText('Failed to create account')).toBeInTheDocument();
    });
  });

  test('shows error snackbar on network error', async () => {
    mockedFetch.mockRejectedValue(new Error('Network error'));

    renderComponent();
    await userEvent.click(screen.getByText('New Account'));
    await userEvent.type(screen.getByLabelText('Display Name'), 'Test Account');
    await userEvent.click(screen.getByText('Create'));

    await waitFor(() => {
      expect(screen.getByText('Error creating account')).toBeInTheDocument();
    });
  });

  test('closes dialog when cancel is clicked', async () => {
    renderComponent();
    await userEvent.click(screen.getByText('New Account'));
    expect(screen.getByText('Create Account')).toBeInTheDocument();
    await userEvent.click(screen.getByText('Cancel'));
    await waitFor(() => {
      expect(screen.queryByText('Create Account')).not.toBeInTheDocument();
    });
  });
});
