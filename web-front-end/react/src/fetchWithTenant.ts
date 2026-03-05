/**
 * Wrapper around fetch that injects the X-Tenant-ID header.
 * All API calls should use this instead of raw fetch().
 */
let currentTenant = 'acme_corp';

export function setCurrentTenant(tenant: string) {
  currentTenant = tenant;
}

export function getCurrentTenant(): string {
  return currentTenant;
}

export function fetchWithTenant(
  input: RequestInfo | URL,
  init?: RequestInit
): Promise<Response> {
  const headers = new Headers(init?.headers);
  headers.set('X-Tenant-ID', currentTenant);
  return fetch(input, { ...init, headers });
}
