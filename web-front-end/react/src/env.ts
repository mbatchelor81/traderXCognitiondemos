/**
 * Build-time tenant ID — baked into the bundle, immutable at runtime.
 * Set via REACT_APP_TENANT_ID environment variable at build time.
 */
export const TENANT_ID = process.env.REACT_APP_TENANT_ID || 'acme_corp';

export const Environment = {
	trade_feed_url: `http://${window.location.hostname}:8000`,
	account_service_url:  `http://${window.location.hostname}:8000`,
	trade_service_url:  `http://${window.location.hostname}:8000`,
	reference_data_url:  `http://${window.location.hostname}:8000`,
	people_service_url:  `http://${window.location.hostname}:8000`,
	position_service_url:  `http://${window.location.hostname}:8000`
}
