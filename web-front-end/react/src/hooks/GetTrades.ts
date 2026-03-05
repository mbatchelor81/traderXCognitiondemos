import { SetStateAction, useEffect, useState } from "react";
import { TradeData } from "../Datatable/types";
import { Environment } from '../env';
import { fetchWithTenant } from '../fetchWithTenant';
import { useTenant } from '../TenantContext';

export const GetTrades = (accountId:number) => {
	const { tenant } = useTenant();
	const [tradesData, setTradesData] = useState<TradeData[]>([]);
	type data = () => Promise<unknown>;

	useEffect(() => {
		let json:SetStateAction<TradeData[]>;
		const fetchData: data = async () => {
			try {
				const response = await fetchWithTenant(`${Environment.position_service_url}/trades/${accountId}`);
				if (response.ok) {
					json = await response.json();
					setTradesData(json);
				}
			} catch (error) {
				return error;
			}
		};
		fetchData();
	}, [accountId, tenant]);
	return tradesData;
}
