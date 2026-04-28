import { useCallback, useEffect, useRef, useState } from "react";
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

const DEFAULT_SUMMARY: AccountSummary = {
	totalTrades: 0,
	settledTrades: 0,
	pendingTrades: 0,
	totalBuyQuantity: 0,
	totalSellQuantity: 0,
	netQuantity: 0,
};

export const GetAccountSummary = (accountId: number): { summary: AccountSummary; refetch: () => void } => {
	const { tenant } = useTenant();
	const [summary, setSummary] = useState<AccountSummary>(DEFAULT_SUMMARY);
	const accountIdRef = useRef(accountId);
	accountIdRef.current = accountId;

	const fetchSummary = useCallback(async () => {
		if (accountIdRef.current === 0) return;
		try {
			const response = await fetchWithTenant(
				`${Environment.account_service_url}/account/${accountIdRef.current}/summary`
			);
			if (response.ok) {
				const json = await response.json();
				setSummary(json);
			}
		} catch {
			// Silently handle fetch errors on refetch
		}
	}, []);

	useEffect(() => {
		if (accountId === 0) {
			setSummary(DEFAULT_SUMMARY);
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
	}, [accountId, tenant]);

	return { summary, refetch: fetchSummary };
};
