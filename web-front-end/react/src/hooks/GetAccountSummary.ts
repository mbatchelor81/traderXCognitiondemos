import { useCallback, useEffect, useRef, useState } from "react";
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
	const abortControllerRef = useRef<AbortController | null>(null);

	const fetchSummary = useCallback(() => {
		if (abortControllerRef.current) {
			abortControllerRef.current.abort();
		}
		if (accountId === 0) {
			setSummary(defaultStatistics);
			return;
		}
		const abortController = new AbortController();
		abortControllerRef.current = abortController;
		const fetchData = async () => {
			try {
				const response = await fetchWithTenant(
					`${Environment.account_service_url}/account/${accountId}/summary`,
					{ signal: abortController.signal },
				);
				if (response.ok && !abortController.signal.aborted) {
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
		return () => {
			if (abortControllerRef.current) {
				abortControllerRef.current.abort();
			}
		};
	}, [fetchSummary]);

	return { data: summary, refetch: fetchSummary };
}
