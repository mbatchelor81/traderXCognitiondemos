import { useCallback, useEffect, useState } from "react";
import { Environment } from '../env';
import { fetchWithTenant } from '../fetchWithTenant';
import { useTenant } from '../TenantContext';

export interface AccountSummary {
	totalTrades: number;
	settledTrades: number;
	pendingTrades: number;
	totalBuyQuantity: number;
	totalSellQuantity: number;
	netQuantity: number;
}

const emptySummary: AccountSummary = {
	totalTrades: 0,
	settledTrades: 0,
	pendingTrades: 0,
	totalBuyQuantity: 0,
	totalSellQuantity: 0,
	netQuantity: 0,
};

export const GetAccountSummary = (accountId: number): { summary: AccountSummary; refetchSummary: () => void } => {
	const { tenant } = useTenant();
	const [summary, setSummary] = useState<AccountSummary>(emptySummary);
	const [refreshKey, setRefreshKey] = useState(0);

	const refetchSummary = useCallback(() => {
		setRefreshKey(prev => prev + 1);
	}, []);

	useEffect(() => {
		if (accountId === 0) {
			setSummary(emptySummary);
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
						setSummary(json);
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

	return { summary, refetchSummary };
}
