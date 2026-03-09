/**
 * Build-time tenant ID — baked into the bundle, immutable at runtime.
 * Set via REACT_APP_TENANT_ID environment variable at build time.
 */
export const TENANT_ID = process.env.REACT_APP_TENANT_ID || 'acme_corp';

/**
 * API base URL — when deployed behind ALB/nginx, all API calls go through
 * the same origin (path-based routing). Set REACT_APP_API_URL at build time
 * to override (e.g., http://ALB_DNS_NAME). Defaults to same-origin.
 */
const API_BASE = process.env.REACT_APP_API_URL || `http://${window.location.hostname}:${window.location.port || '80'}`;

export const Environment = {
	trade_feed_url: API_BASE,
	account_service_url:  API_BASE,
	trade_service_url:  API_BASE,
	reference_data_url:  API_BASE,
	people_service_url:  API_BASE,
	position_service_url:  API_BASE
}
