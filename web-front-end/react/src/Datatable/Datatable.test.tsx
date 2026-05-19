import React from 'react';
import { render, screen } from '@testing-library/react';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import { Datatable } from './Datatable';
import { TenantProvider } from '../TenantContext';
import { fetchWithTenant } from '../fetchWithTenant';

jest.mock('../fetchWithTenant', () => ({
  fetchWithTenant: jest.fn(),
}));

jest.mock('../socket', () => ({
  socket: {
    on: jest.fn(),
    off: jest.fn(),
    emit: jest.fn(),
  },
}));

jest.mock('ag-grid-react', () => ({
  AgGridReact: ({ rowData, columnDefs }: { rowData: unknown[]; columnDefs: unknown[] }) => (
    <div data-testid="ag-grid">
      <span data-testid="row-count">{Array.isArray(rowData) ? rowData.length : 0}</span>
      <span data-testid="col-count">{Array.isArray(columnDefs) ? columnDefs.length : 0}</span>
    </div>
  ),
}));

const mockedFetch = fetchWithTenant as jest.MockedFunction<typeof fetchWithTenant>;
const theme = createTheme();

const renderComponent = () =>
  render(
    <ThemeProvider theme={theme}>
      <TenantProvider>
        <Datatable />
      </TenantProvider>
    </ThemeProvider>
  );

describe('Datatable', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockedFetch.mockResolvedValue({
      ok: true,
      json: async () => [],
    } as Response);
  });

  test('renders account selector section', () => {
    renderComponent();
    expect(screen.getAllByText('Select Account').length).toBeGreaterThan(0);
  });

  test('renders action buttons', () => {
    renderComponent();
    expect(screen.getByText('New Trade')).toBeInTheDocument();
    expect(screen.getByText('New Account')).toBeInTheDocument();
    expect(screen.getByText('Add User')).toBeInTheDocument();
  });

  test('shows empty state when no account is selected', () => {
    renderComponent();
    expect(screen.getByText('No Account Selected')).toBeInTheDocument();
    expect(
      screen.getByText('Select an account from the dropdown above to view trades and positions')
    ).toBeInTheDocument();
  });

  test('New Trade button is disabled when no account is selected', () => {
    renderComponent();
    expect(screen.getByRole('button', { name: /New Trade/i })).toBeDisabled();
  });
});
