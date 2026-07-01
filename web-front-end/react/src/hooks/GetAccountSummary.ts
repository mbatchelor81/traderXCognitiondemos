import { useEffect, useState } from "react";
import { AccountSummary, AccountSummaryStatistics } from "../Datatable/types";
import { Environment } from '../env';
import { fetchWithTenant } from '../fetchWithTenant';
import { useTenant } from '../TenantContext';

const EMPTY_STATISTICS: AccountSummaryStatistics = {
	totalTrades: 0,
	settledTrades: 0,
	pendingTrades: 0,
	totalBuyQuantity: 0,
	totalSellQuantity: 0,
	netQuantity: 0,
};

export const GetAccountSummary = (accountId: number, refreshKey: number = 0) => {
	const { tenant } = useTenant();
	const [statistics, setStatistics] = useState<AccountSummaryStatistics>(EMPTY_STATISTICS);
	useEffect(() => {
		if (accountId === 0) {
			setStatistics(EMPTY_STATISTICS);
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
						setStatistics(json.statistics ?? EMPTY_STATISTICS);
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
	}, [accountId, tenant, refreshKey]);
	return statistics;
}
