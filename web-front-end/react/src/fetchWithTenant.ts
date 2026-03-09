/**
 * Tenant ID is set at build time via REACT_APP_TENANT_ID.
 * No runtime tenant switching — each deployment serves one tenant.
 */
export const TENANT_ID: string = process.env.REACT_APP_TENANT_ID || 'default_tenant';
