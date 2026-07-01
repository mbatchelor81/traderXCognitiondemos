import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { TenantProvider, useTenant, TENANTS } from './TenantContext';

const TestConsumer = () => {
  const { tenant, setTenant } = useTenant();
  return (
    <div>
      <span data-testid="tenant">{tenant}</span>
      <button onClick={() => setTenant('globex_inc')}>Switch Tenant</button>
    </div>
  );
};

describe('TenantContext', () => {
  test('provides default tenant as acme_corp', () => {
    render(
      <TenantProvider>
        <TestConsumer />
      </TenantProvider>
    );
    expect(screen.getByTestId('tenant')).toHaveTextContent('acme_corp');
  });

  test('allows switching tenant via setTenant', async () => {
    render(
      <TenantProvider>
        <TestConsumer />
      </TenantProvider>
    );
    await userEvent.click(screen.getByText('Switch Tenant'));
    expect(screen.getByTestId('tenant')).toHaveTextContent('globex_inc');
  });

  test('exports expected tenant list', () => {
    expect(TENANTS).toEqual(['acme_corp', 'globex_inc', 'initech']);
  });

  test('useTenant returns default context when used outside provider', () => {
    render(<TestConsumer />);
    expect(screen.getByTestId('tenant')).toHaveTextContent('acme_corp');
  });
});
