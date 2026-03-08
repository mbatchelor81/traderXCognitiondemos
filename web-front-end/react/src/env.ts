// When served behind the ALB, all services are accessible via the same origin
// using path-based routing. The ALB routes /account/*, /people/* to users-service
// and /trade/*, /trades/*, /positions/*, /stocks/* to trades-service.
const BASE_URL = window.location.origin;

export const Environment = {
	trade_feed_url: BASE_URL,
	account_service_url:  BASE_URL,
	trade_service_url:  BASE_URL,
	reference_data_url:  BASE_URL,
	people_service_url:  BASE_URL,
	position_service_url:  BASE_URL
}
