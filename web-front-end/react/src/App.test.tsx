import React from 'react';
import { render, screen } from '@testing-library/react';
import { ThemeProvider } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import App from './App';
import theme from './theme';

const renderApp = () =>
  render(
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <App />
    </ThemeProvider>
  );

test('renders TraderX header', () => {
  renderApp();
  const headerElement = screen.getByText(/TraderX/i);
  expect(headerElement).toBeInTheDocument();
});

test('renders the build-time tenant name', () => {
  renderApp();
  expect(screen.getByTestId('tenant-name')).toHaveTextContent('Test Tenant');
});
