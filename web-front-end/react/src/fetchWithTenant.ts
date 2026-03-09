/**
 * Simple fetch wrapper for API calls.
 * In single-tenant mode, no tenant header is needed —
 * tenant isolation is enforced at the infrastructure level.
 */
export function fetchWithTenant(
  input: RequestInfo | URL,
  init?: RequestInit
): Promise<Response> {
  return fetch(input, init);
}
