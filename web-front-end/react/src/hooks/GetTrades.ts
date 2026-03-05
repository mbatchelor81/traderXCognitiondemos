import { useEffect, useState } from "react";
import { TradeData } from "../Datatable/types";
import { Environment } from '../env';
import { fetchWithTenant } from '../fetchWithTenant';
import { useTenant } from '../TenantContext';

export const GetTrades = (accountId:number) => {
	const { tenant } = useTenant();
	const [tradesData, setTradesData] = useState<TradeData[]>([]);
	useEffect(() => {
		if (accountId === 0) {
			setTradesData([]);
			return;
		}
		const abortController = new AbortController();
		const fetchData = async () => {
			try {
				const response = await fetchWithTenant(
					`${Environment.position_service_url}/trades/${accountId}`,
					{ signal: abortController.signal }
				);
				if (response.ok) {
					const json = await response.json();
					if (!abortController.signal.aborted) {
						setTradesData(json);
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
	return tradesData;
}
