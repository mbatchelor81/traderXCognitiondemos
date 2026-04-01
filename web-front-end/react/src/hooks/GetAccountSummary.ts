import { useCallback, useEffect, useState } from "react";
import { Environment } from '../env';
import { fetchWithTenant } from '../fetchWithTenant';
import { useTenant } from '../TenantContext';

export interface AccountSummaryStatistics {
	totalTrades: number;
	settledTrades: number;
	pendingTrades: number;
	totalBuyQuantity: number;
	totalSellQuantity: number;
	netQuantity: number;
}

export interface AccountSummaryData {
	account: Record<string, unknown>;
	users: Record<string, unknown>[];
	positions: Record<string, unknown>[];
	statistics: AccountSummaryStatistics;
}

const defaultStatistics: AccountSummaryStatistics = {
	totalTrades: 0,
	settledTrades: 0,
	pendingTrades: 0,
	totalBuyQuantity: 0,
	totalSellQuantity: 0,
	netQuantity: 0,
};

export const GetAccountSummary = (accountId: number): { data: AccountSummaryStatistics; refetch: () => void } => {
	const { tenant } = useTenant();
	const [summary, setSummary] = useState<AccountSummaryStatistics>(defaultStatistics);

	const fetchSummary = useCallback(() => {
		if (accountId === 0) {
			setSummary(defaultStatistics);
			return;
		}
		const fetchData = async () => {
			try {
				const response = await fetchWithTenant(
					`${Environment.account_service_url}/account/${accountId}/summary`,
				);
				if (response.ok) {
					const json: AccountSummaryData = await response.json();
					setSummary(json.statistics);
				}
			} catch (error) {
				if (error instanceof DOMException && error.name === 'AbortError') {
					return;
				}
			}
		};
		fetchData();
		// eslint-disable-next-line react-hooks/exhaustive-deps
	}, [accountId, tenant]);

	useEffect(() => {
		fetchSummary();
	}, [fetchSummary]);

	return { data: summary, refetch: fetchSummary };
}
