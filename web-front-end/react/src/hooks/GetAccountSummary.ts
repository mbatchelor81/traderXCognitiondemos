import { useEffect, useState } from "react";
import { Environment } from '../env';
import { fetchWithTenant } from '../fetchWithTenant';
import { useTenant } from '../TenantContext';

export interface AccountSummaryStats {
	totalTrades: number;
	settledTrades: number;
	pendingTrades: number;
	totalBuyQuantity: number;
	totalSellQuantity: number;
	netQuantity: number;
}

export interface AccountSummary {
	account: Record<string, unknown>;
	users: Record<string, unknown>[];
	positions: Record<string, unknown>[];
	statistics: AccountSummaryStats;
}

const EMPTY_STATS: AccountSummaryStats = {
	totalTrades: 0,
	settledTrades: 0,
	pendingTrades: 0,
	totalBuyQuantity: 0,
	totalSellQuantity: 0,
	netQuantity: 0,
};

export const GetAccountSummary = (accountId: number, refreshKey: number = 0) => {
	const { tenant } = useTenant();
	const [summary, setSummary] = useState<AccountSummaryStats>(EMPTY_STATS);

	useEffect(() => {
		if (accountId === 0) {
			setSummary(EMPTY_STATS);
			return;
		}
		const abortController = new AbortController();
		const fetchData = async () => {
			try {
				const response = await fetchWithTenant(
					`${Environment.account_service_url}/account/${accountId}/summary`,
					{ signal: abortController.signal }
				);
				if (response.ok) {
					const json: AccountSummary = await response.json();
					if (!abortController.signal.aborted) {
						setSummary(json.statistics);
					}
				}
			} catch (error) {
				if (error instanceof DOMException && error.name === 'AbortError') {
					return;
				}
				return error;
			}
		};
		fetchData();
		return () => { abortController.abort(); };
	}, [accountId, tenant, refreshKey]);

	return summary;
};
