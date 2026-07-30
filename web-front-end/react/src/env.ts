/**
 * Build-time environment configuration.
 *
 * The tenant is baked into the bundle at build time via REACT_APP_TENANT_ID and
 * is immutable at runtime — each deployment serves exactly one tenant.
 */

const tenantId = process.env.REACT_APP_TENANT_ID;

if (!tenantId) {
	throw new Error(
		'REACT_APP_TENANT_ID must be set at build time — each build serves exactly one tenant.'
	);
}

export const TENANT_ID: string = tenantId;

const host = typeof window !== 'undefined' ? window.location.hostname : 'localhost';

const serviceUrl = (override: string | undefined, port: number) => override || `http://${host}:${port}`;

/**
 * Extracted domain service URLs. Defaults are the local service ports; Process B
 * re-points these at the API gateway / ALB via the build-time overrides.
 */
export const Environment = {
	account_service_url: serviceUrl(process.env.REACT_APP_ACCOUNT_SERVICE_URL, 8001),
	trade_service_url: serviceUrl(process.env.REACT_APP_TRADING_SERVICE_URL, 8002),
	trade_feed_url: serviceUrl(process.env.REACT_APP_TRADING_SERVICE_URL, 8002),
	position_service_url: serviceUrl(process.env.REACT_APP_POSITION_SERVICE_URL, 8003),
	reference_data_url: serviceUrl(process.env.REACT_APP_REFERENCE_DATA_SERVICE_URL, 8004),
	people_service_url: serviceUrl(process.env.REACT_APP_PEOPLE_SERVICE_URL, 8005),
};
