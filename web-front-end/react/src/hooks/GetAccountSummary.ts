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

const defaultStats: AccountSummaryStats = {
	totalTrades: 0,
	settledTrades: 0,
	pendingTrades: 0,
	totalBuyQuantity: 0,
	totalSellQuantity: 0,
	netQuantity: 0,
};

export const GetAccountSummary = (accountId: number) => {
	const { tenant } = useTenant();
	const [summary, setSummary] = useState<AccountSummaryStats>(defaultStats);

	const refetchSummary = useCallback(() => {
		if (accountId === 0) {
			setSummary(defaultStats);
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
					const json = await response.json();
					if (!abortController.signal.aborted) {
						setSummary(json.statistics ?? defaultStats);
					}
				}
			} catch (error) {
				if (error instanceof DOMException && error.name === 'AbortError') {
					return;
				}
			}
		};
		fetchData();
		return () => { abortController.abort(); };
	}, [accountId, tenant]);

	useEffect(() => {
		refetchSummary();
	}, [refetchSummary]);

	return { summary, refetchSummary };
};
