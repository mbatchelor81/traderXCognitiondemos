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

export const GetAccountSummary = (accountId: number): { summary: AccountSummary; refetch: () => void } => {
	const { tenant } = useTenant();
	const [summary, setSummary] = useState<AccountSummary>(emptySummary);

	const fetchSummary = useCallback(async (signal?: AbortSignal) => {
		if (accountId === 0) {
			setSummary(emptySummary);
			return;
		}
		try {
			const response = await fetchWithTenant(
				`${Environment.account_service_url}/account/${accountId}/summary`,
				signal ? { signal } : undefined
			);
			if (response.ok) {
				const json = await response.json();
				if (!signal?.aborted) {
					setSummary(json);
				}
			}
		} catch (error) {
			if (error instanceof DOMException && error.name === 'AbortError') {
				return;
			}
		}
	}, [accountId, tenant]);

	useEffect(() => {
		const abortController = new AbortController();
		fetchSummary(abortController.signal);
		return () => { abortController.abort(); };
	}, [fetchSummary]);

	const refetch = useCallback(() => {
		fetchSummary();
	}, [fetchSummary]);

	return { summary, refetch };
}
