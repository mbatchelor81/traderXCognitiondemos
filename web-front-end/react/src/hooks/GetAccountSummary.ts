import { useCallback, useEffect, useState } from "react";
import { AccountSummaryData } from "../Datatable/types";
import { Environment } from '../env';
import { fetchWithTenant } from '../fetchWithTenant';
import { useTenant } from '../TenantContext';

const EMPTY_SUMMARY: AccountSummaryData = {
	totalTrades: 0,
	settledTrades: 0,
	pendingTrades: 0,
	totalBuyQuantity: 0,
	totalSellQuantity: 0,
	netQuantity: 0,
};

export const GetAccountSummary = (accountId: number) => {
	const { tenant } = useTenant();
	const [summaryData, setSummaryData] = useState<AccountSummaryData>(EMPTY_SUMMARY);
	const [refreshKey, setRefreshKey] = useState(0);

	const refetch = useCallback(() => {
		setRefreshKey(k => k + 1);
	}, []);

	useEffect(() => {
		if (accountId === 0) {
			setSummaryData(EMPTY_SUMMARY);
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
					return;
				}
				return error;
			}
		};
		fetchData();
		return () => { abortController.abort(); };
	}, [accountId, tenant, refreshKey]);

	return { summaryData, refetch };
}
