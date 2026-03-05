import './App.css';
import { Datatable } from './Datatable/Datatable';
import React from 'react';
import { TenantProvider, useTenant, TENANTS, TenantId } from './TenantContext';
import { setCurrentTenant } from './fetchWithTenant';
import { reconnectSocket } from './socket';
import FormControl from '@mui/material/FormControl';
import InputLabel from '@mui/material/InputLabel';
import Select, { SelectChangeEvent } from '@mui/material/Select';
import MenuItem from '@mui/material/MenuItem';

const TenantSelector = () => {
  const { tenant, setTenant } = useTenant();

  const handleTenantChange = (event: SelectChangeEvent<string>) => {
    const newTenant = event.target.value as TenantId;
    setCurrentTenant(newTenant);
    reconnectSocket(newTenant);
    setTenant(newTenant);
  };

  return (
    <FormControl sx={{ m: 1, minWidth: 160 }} size="small">
      <InputLabel>Tenant</InputLabel>
      <Select
        value={tenant}
        label="Tenant"
        onChange={handleTenantChange}
      >
        {TENANTS.map((t) => (
          <MenuItem key={t} value={t}>
            {t}
          </MenuItem>
        ))}
      </Select>
    </FormControl>
  );
};

function App() {
  return (
    <TenantProvider>
      <div className="App">
        <div className="app-header" style={{ display: 'flex', alignItems: 'center', padding: '8px 16px', borderBottom: '1px solid #e0e0e0' }}>
          <h3 style={{ margin: 0, marginRight: 'auto' }}>TraderX</h3>
          <TenantSelector />
        </div>
        <Datatable />
      </div>
    </TenantProvider>
  );
}

export default App;
