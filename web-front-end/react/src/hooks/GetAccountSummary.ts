import { useCallback, useEffect, useState } from "react";
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

interface AccountSummaryResponse {
	account: Record<string, unknown>;
	users: Record<string, unknown>[];
	positions: Record<string, unknown>[];
	statistics: AccountSummaryStats;
}

const emptyStats: AccountSummaryStats = {
	totalTrades: 0,
	settledTrades: 0,
	pendingTrades: 0,
	totalBuyQuantity: 0,
	totalSellQuantity: 0,
	netQuantity: 0,
};

export interface AccountSummaryResult {
	stats: AccountSummaryStats;
	refresh: () => void;
}

export const GetAccountSummary = (accountId: number): AccountSummaryResult => {
	const { tenant } = useTenant();
	const [stats, setStats] = useState<AccountSummaryStats>(emptyStats);
	const [refreshCounter, setRefreshCounter] = useState(0);

	const refresh = useCallback(() => {
		setRefreshCounter((c) => c + 1);
	}, []);

	useEffect(() => {
		if (accountId === 0) {
			setStats(emptyStats);
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
					const json: AccountSummaryResponse = await response.json();
					if (!abortController.signal.aborted) {
						setStats(json.statistics);
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
	}, [accountId, tenant, refreshCounter]);

	return { stats, refresh };
};
