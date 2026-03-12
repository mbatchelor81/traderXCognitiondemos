/**
 * Build-time tenant ID — baked into the bundle, immutable at runtime.
 * Set via REACT_APP_TENANT_ID environment variable at build time.
 */
export const TENANT_ID = process.env.REACT_APP_TENANT_ID || 'acme_corp';

/**
 * When REACT_APP_USE_ALB_ROUTING is set (or when running on a non-default port
 * like 80/443 behind an ALB), use path-based routing through the ALB origin.
 * Otherwise fall back to direct service ports for local development.
 */
const isLocalDev =
	typeof window !== 'undefined' &&
	(window.location.port === '18094' || window.location.port === '3000');

const useAlbRouting =
	process.env.REACT_APP_USE_ALB_ROUTING === 'true' || !isLocalDev;

const origin = typeof window !== 'undefined' ? window.location.origin : '';

export const Environment = useAlbRouting
	? {
			trade_feed_url: origin,
			account_service_url: origin,
			trade_service_url: origin,
			reference_data_url: origin,
			people_service_url: origin,
			position_service_url: origin,
		}
	: {
			trade_feed_url: `http://${window.location.hostname}:8002`,
			account_service_url: `http://${window.location.hostname}:8001`,
			trade_service_url: `http://${window.location.hostname}:8002`,
			reference_data_url: `http://${window.location.hostname}:8004`,
			people_service_url: `http://${window.location.hostname}:8005`,
			position_service_url: `http://${window.location.hostname}:8003`,
		};
