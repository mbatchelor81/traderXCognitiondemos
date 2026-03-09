import './App.css';
import { Datatable } from './Datatable/Datatable';
import React, { useEffect, useState } from 'react';
import { TENANT_ID } from './env';
import { socket } from './socket';
import AppBar from '@mui/material/AppBar';
import Toolbar from '@mui/material/Toolbar';
import Typography from '@mui/material/Typography';
import Box from '@mui/material/Box';
import Chip from '@mui/material/Chip';
import ShowChartIcon from '@mui/icons-material/ShowChart';
import FiberManualRecordIcon from '@mui/icons-material/FiberManualRecord';

const ConnectionStatus = () => {
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    const checkConnection = () => {
      setConnected(socket.connected);
    };

    const onConnect = () => setConnected(true);
    const onDisconnect = () => setConnected(false);

    checkConnection();
    const interval = setInterval(checkConnection, 2000);

    socket.on('connect', onConnect);
    socket.on('disconnect', onDisconnect);

    return () => {
      clearInterval(interval);
      socket.off('connect', onConnect);
      socket.off('disconnect', onDisconnect);
    };
  }, []);

  return (
    <Chip
      icon={
        <FiberManualRecordIcon
          sx={{ fontSize: 10, color: connected ? '#10b981' : '#ef4444' }}
        />
      }
      label={connected ? 'Connected' : 'Disconnected'}
      size="small"
      variant="outlined"
      sx={{
        borderColor: 'rgba(255,255,255,0.15)',
        color: '#9ca3af',
        fontSize: '0.75rem',
        height: 28,
        '& .MuiChip-icon': { marginLeft: '8px' },
      }}
    />
  );
};

/** Format tenant ID for display: "acme_corp" → "Acme Corp" */
const formatTenantName = (id: string) =>
  id.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());

function App() {
  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh', bgcolor: 'background.default' }}>
      <AppBar
        position="static"
        elevation={0}
        sx={{
          bgcolor: '#0d1321',
          borderBottom: '1px solid rgba(255,255,255,0.08)',
        }}
      >
        <Toolbar sx={{ justifyContent: 'space-between', minHeight: '56px !important' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
            <ShowChartIcon sx={{ color: '#3b82f6', fontSize: 28 }} />
            <Typography
              variant="h6"
              sx={{
                fontWeight: 700,
                letterSpacing: '-0.02em',
                background: 'linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
              }}
            >
              TraderX
            </Typography>
          </Box>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <ConnectionStatus />
            <Chip
              label={formatTenantName(TENANT_ID)}
              size="small"
              sx={{
                bgcolor: 'rgba(59, 130, 246, 0.15)',
                color: '#3b82f6',
                fontWeight: 600,
                fontSize: '0.75rem',
                height: 28,
                border: '1px solid rgba(59, 130, 246, 0.3)',
              }}
            />
          </Box>
        </Toolbar>
      </AppBar>
      <Box sx={{ flex: 1, overflow: 'auto' }}>
        <Datatable />
      </Box>
    </Box>
  );
}

export default App;
