import React, { createContext, useContext, useState, useCallback, ReactNode } from 'react';

export const TENANTS = ['acme_corp', 'globex_inc', 'initech'] as const;
export type TenantId = typeof TENANTS[number];

interface TenantContextValue {
  tenant: TenantId;
  setTenant: (tenant: TenantId) => void;
}

const TenantContext = createContext<TenantContextValue>({
  tenant: 'acme_corp',
  setTenant: () => {},
});

export const useTenant = () => useContext(TenantContext);

interface TenantProviderProps {
  children: ReactNode;
}

export const TenantProvider = ({ children }: TenantProviderProps) => {
  const [tenant, setTenantState] = useState<TenantId>('acme_corp');

  const setTenant = useCallback((newTenant: TenantId) => {
    setTenantState(newTenant);
  }, []);

  return (
    <TenantContext.Provider value={{ tenant, setTenant }}>
      {children}
    </TenantContext.Provider>
  );
};
