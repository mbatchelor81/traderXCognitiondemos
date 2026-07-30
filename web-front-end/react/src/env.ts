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

export const Environment = {
	trade_feed_url: `http://${host}:8000`,
	account_service_url: `http://${host}:8000`,
	trade_service_url: `http://${host}:8000`,
	reference_data_url: `http://${host}:8000`,
	people_service_url: `http://${host}:8000`,
	position_service_url: `http://${host}:8000`,
};
