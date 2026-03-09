/**
 * Single-tenant fetch wrapper.
 * In single-tenant mode the backend middleware enforces the tenant,
 * so we just delegate to plain fetch(). This module is kept as a
 * thin wrapper so call-sites don't need to change.
 */
export function fetchWithTenant(
  input: RequestInfo | URL,
  init?: RequestInit
): Promise<Response> {
  return fetch(input, init);
}
