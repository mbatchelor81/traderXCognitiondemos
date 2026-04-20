import { useEffect, useState, useRef, useCallback } from "react";
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

export const GetAccountSummary = (accountId: number) => {
	const { tenant } = useTenant();
	const [summary, setSummary] = useState<AccountSummary>(emptySummary);
	const accountIdRef = useRef(accountId);
	accountIdRef.current = accountId;

	const refetch = useCallback(() => {
		if (accountIdRef.current === 0) return;
		const controller = new AbortController();
		fetchWithTenant(
			`${Environment.account_service_url}/account/${accountIdRef.current}/summary`,
			{ signal: controller.signal }
		)
			.then(res => {
				if (res.ok) return res.json();
				return null;
			})
			.then(json => {
				if (json && json.statistics && !controller.signal.aborted) {
					setSummary(json.statistics);
				}
			})
			.catch(err => {
				if (err instanceof DOMException && err.name === 'AbortError') return;
			});
		return controller;
	}, []);

	useEffect(() => {
		if (accountId === 0) {
			setSummary(emptySummary);
			return;
		}
		const controller = refetch();
		return () => { controller?.abort(); };
	}, [accountId, tenant, refetch]);

	return { summary, refetch };
};
