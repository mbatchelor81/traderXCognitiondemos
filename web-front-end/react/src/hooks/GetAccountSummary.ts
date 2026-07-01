import { useCallback, useEffect, useState } from "react";
import { Environment } from '../env';
import { fetchWithTenant } from '../fetchWithTenant';
import { useTenant } from '../TenantContext';

export interface AccountSummary {
	statistics: {
		totalTrades: number;
		settledTrades: number;
		pendingTrades: number;
		totalBuyQuantity: number;
		totalSellQuantity: number;
		netQuantity: number;
	};
}

const defaultSummary: AccountSummary = {
	statistics: {
		totalTrades: 0,
		settledTrades: 0,
		pendingTrades: 0,
		totalBuyQuantity: 0,
		totalSellQuantity: 0,
		netQuantity: 0,
	},
};

export interface AccountSummaryResult {
	summary: AccountSummary;
	refetch: () => void;
}

export const GetAccountSummary = (accountId: number): AccountSummaryResult => {
	const { tenant } = useTenant();
	const [summary, setSummary] = useState<AccountSummary>(defaultSummary);
	const [refreshKey, setRefreshKey] = useState(0);

	const refetch = useCallback(() => {
		setRefreshKey(k => k + 1);
	}, []);

	useEffect(() => {
		if (accountId === 0) {
			setSummary(defaultSummary);
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

	return { summary, refetch };
};
