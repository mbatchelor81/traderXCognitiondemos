import { useEffect, useState } from "react";
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

export const GetAccountSummary = (accountId: number) => {
	const { tenant } = useTenant();
	const [summaryData, setSummaryData] = useState<AccountSummaryData | null>(null);
	useEffect(() => {
		if (accountId === 0) {
			setSummaryData(null);
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
						setSummaryData(json);
					}
				}
			} catch (error) {
				if (error instanceof DOMException && error.name === 'AbortError') {
					return; // Expected when effect is superseded
				}
				return error;
			}
		};
		fetchData();
		return () => { abortController.abort(); };
	}, [accountId, tenant]);
	return summaryData;
}
