import React from 'react';
import { render, screen } from '@testing-library/react';
import { ThemeProvider } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import App from './App';
import theme from './theme';

test('renders TraderX header', () => {
  render(
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <App />
    </ThemeProvider>
  );
  const headerElement = screen.getByText(/TraderX/i);
  expect(headerElement).toBeInTheDocument();
});

test('renders tenant name from build-time env var', () => {
  render(
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <App />
    </ThemeProvider>
  );
  // In single-tenant mode the tenant name is displayed as a static chip
  // Default REACT_APP_TENANT_ID is 'acme_corp' → displayed as 'Acme Corp'
  const tenantChip = screen.getByText(/Acme Corp/i);
  expect(tenantChip).toBeInTheDocument();
});
