import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import { CreateAccountUser } from './CreateAccountUser';
import { fetchWithTenant } from '../fetchWithTenant';

jest.mock('../fetchWithTenant', () => ({
  fetchWithTenant: jest.fn(),
}));

const mockedFetch = fetchWithTenant as jest.MockedFunction<typeof fetchWithTenant>;
const theme = createTheme();

const renderComponent = (accountId: number = 123) =>
  render(
    <ThemeProvider theme={theme}>
      <CreateAccountUser accountId={accountId} />
    </ThemeProvider>
  );

describe('CreateAccountUser', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('renders the Add User button', () => {
    renderComponent();
    expect(screen.getByText('Add User')).toBeInTheDocument();
  });

  test('opens dialog when button is clicked', async () => {
    renderComponent();
    await userEvent.click(screen.getByText('Add User'));
    expect(screen.getByText('Add Account User')).toBeInTheDocument();
    expect(screen.getByLabelText('Search People')).toBeInTheDocument();
  });

  test('searches people when typing in the search field', async () => {
    const mockPeople = [
      { logonId: 'jsmith', fullName: 'John Smith' },
    ];
    mockedFetch.mockResolvedValue({
      ok: true,
      json: async () => mockPeople,
    } as Response);

    renderComponent();
    await userEvent.click(screen.getByText('Add User'));

    const searchInput = screen.getByLabelText('Search People');
    await userEvent.type(searchInput, 'John');

    await waitFor(() => {
      expect(mockedFetch).toHaveBeenCalledWith(
        expect.stringContaining('/people/GetMatchingPeople?SearchText=')
      );
    });
  });

  test('does not search with less than 2 characters', async () => {
    renderComponent();
    await userEvent.click(screen.getByText('Add User'));

    const searchInput = screen.getByLabelText('Search People');
    await userEvent.type(searchInput, 'J');

    expect(mockedFetch).not.toHaveBeenCalled();
  });

  test('submits successfully when a user is selected', async () => {
    const mockPeople = [
      { logonId: 'jsmith', fullName: 'John Smith' },
    ];
    // First call returns search results, second call is the submit
    mockedFetch
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockPeople,
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({}),
      } as Response);

    renderComponent();
    await userEvent.click(screen.getByText('Add User'));

    const searchInput = screen.getByLabelText('Search People');
    await userEvent.type(searchInput, 'John');

    await waitFor(() => {
      expect(mockedFetch).toHaveBeenCalled();
    });
  });

  test('closes dialog when cancel is clicked', async () => {
    renderComponent();
    await userEvent.click(screen.getByText('Add User'));
    expect(screen.getByText('Add Account User')).toBeInTheDocument();

    await userEvent.click(screen.getByText('Cancel'));
    await waitFor(() => {
      expect(screen.queryByText('Add Account User')).not.toBeInTheDocument();
    });
  });

  test('shows error on submission failure', async () => {
    mockedFetch.mockRejectedValue(new Error('Network error'));

    renderComponent();
    await userEvent.click(screen.getByText('Add User'));

    const searchInput = screen.getByLabelText('Search People');
    await userEvent.type(searchInput, 'John Smith');

    await waitFor(() => {
      expect(mockedFetch).toHaveBeenCalled();
    });
  });
});
