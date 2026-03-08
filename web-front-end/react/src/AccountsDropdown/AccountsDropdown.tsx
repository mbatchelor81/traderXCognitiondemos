import React from 'react';
import MenuItem from '@mui/material/MenuItem';
import FormControl from '@mui/material/FormControl';
import Select from '@mui/material/Select';
import InputLabel from '@mui/material/InputLabel';
import Chip from '@mui/material/Chip';
import Box from '@mui/material/Box';
import { GetAccounts } from '../hooks';
import { AccountData, AccountsDropdownProps } from './types';

export const AccountsDropdown = ({ handleChange, currentAccount }: AccountsDropdownProps) => {
  const accounts = GetAccounts();

  return (
    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
      <FormControl size="small" sx={{ minWidth: 240 }}>
        <InputLabel
          sx={{
            color: '#9ca3af',
            '&.Mui-focused': { color: '#3b82f6' },
          }}
        >
          Select Account
        </InputLabel>
        <Select
          value={currentAccount}
          label="Select Account"
          onChange={handleChange}
          sx={{
            color: '#e5e7eb',
            '.MuiOutlinedInput-notchedOutline': {
              borderColor: 'rgba(255,255,255,0.15)',
            },
            '&:hover .MuiOutlinedInput-notchedOutline': {
              borderColor: 'rgba(255,255,255,0.3)',
            },
            '&.Mui-focused .MuiOutlinedInput-notchedOutline': {
              borderColor: '#3b82f6',
            },
            '.MuiSvgIcon-root': { color: '#9ca3af' },
          }}
        >
          <MenuItem value="">
            <em style={{ color: '#6b7280' }}>None</em>
          </MenuItem>
          {accounts.map((account: AccountData) => (
            <MenuItem key={account.id} value={account.id}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <span>{account.displayName}</span>
                <span style={{ color: '#6b7280', fontSize: '0.8rem' }}>#{account.id}</span>
              </Box>
            </MenuItem>
          ))}
        </Select>
      </FormControl>
      <Chip
        label={`${accounts.length} accounts`}
        size="small"
        sx={{
          bgcolor: 'rgba(59, 130, 246, 0.1)',
          color: '#3b82f6',
          fontSize: '0.7rem',
          height: 24,
          border: '1px solid rgba(59, 130, 246, 0.2)',
        }}
      />
    </Box>
  );
};
