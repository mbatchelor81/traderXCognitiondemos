import { createTheme, Theme } from '@mui/material/styles';

const THEME_STORAGE_KEY = 'traderx-theme-mode';

export type ThemeMode = 'light' | 'dark';

export function getStoredThemeMode(): ThemeMode {
  const stored = localStorage.getItem(THEME_STORAGE_KEY);
  if (stored === 'light' || stored === 'dark') {
    return stored;
  }
  return 'dark';
}

export function storeThemeMode(mode: ThemeMode): void {
  localStorage.setItem(THEME_STORAGE_KEY, mode);
}

const darkTheme = createTheme({
  palette: {
    mode: 'dark',
    primary: { main: '#3b82f6' },
    secondary: { main: '#8b5cf6' },
    background: { default: '#0a0e17', paper: '#111827' },
    success: { main: '#10b981' },
    error: { main: '#ef4444' },
    text: { primary: '#e5e7eb', secondary: '#9ca3af' },
  },
  typography: {
    fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
  },
  shape: { borderRadius: 8 },
  components: {
    MuiCard: {
      styleOverrides: {
        root: {
          backgroundImage: 'none',
          border: '1px solid rgba(255,255,255,0.08)',
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: 'none',
          fontWeight: 600,
        },
      },
    },
    MuiDialog: {
      styleOverrides: {
        paper: {
          backgroundImage: 'none',
          border: '1px solid rgba(255,255,255,0.1)',
        },
      },
    },
  },
});

const lightTheme = createTheme({
  palette: {
    mode: 'light',
    primary: { main: '#2563eb' },
    secondary: { main: '#7c3aed' },
    background: { default: '#f3f4f6', paper: '#ffffff' },
    success: { main: '#059669' },
    error: { main: '#dc2626' },
    text: { primary: '#111827', secondary: '#4b5563' },
  },
  typography: {
    fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
  },
  shape: { borderRadius: 8 },
  components: {
    MuiCard: {
      styleOverrides: {
        root: {
          backgroundImage: 'none',
          border: '1px solid rgba(0,0,0,0.12)',
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: 'none',
          fontWeight: 600,
        },
      },
    },
    MuiDialog: {
      styleOverrides: {
        paper: {
          backgroundImage: 'none',
          border: '1px solid rgba(0,0,0,0.12)',
        },
      },
    },
  },
});

export function getTheme(mode: ThemeMode): Theme {
  return mode === 'dark' ? darkTheme : lightTheme;
}

// Default export for backward compatibility
export default darkTheme;
