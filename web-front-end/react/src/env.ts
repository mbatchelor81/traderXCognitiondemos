/**
 * Build-time tenant ID — baked into the bundle, immutable at runtime.
 * Set via REACT_APP_TENANT_ID environment variable at build time.
 */
export const TENANT_ID = process.env.REACT_APP_TENANT_ID || 'acme_corp';

export const Environment = {
	trade_feed_url: `http://${window.location.hostname}:8002`,
	account_service_url:  `http://${window.location.hostname}:8001`,
	trade_service_url:  `http://${window.location.hostname}:8002`,
	reference_data_url:  `http://${window.location.hostname}:8004`,
	people_service_url:  `http://${window.location.hostname}:8005`,
	position_service_url:  `http://${window.location.hostname}:8003`
}
