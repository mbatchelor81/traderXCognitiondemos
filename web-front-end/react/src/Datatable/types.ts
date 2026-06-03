export type TradeSide = 'Buy' | 'Sell';

export interface TradeData {
	id?: string;
	accountId?: number;
	security: string;
	side?: TradeSide;
	state?: string;
	quantity: number;
	updated?: Date;
	created?: Date;
}

export interface PositionData {
	accountId: number;
	security: string;
	quantity: number;
	updated: Date;
}

export interface AccountStatistics {
	totalTrades: number;
	settledTrades: number;
	pendingTrades: number;
	totalBuyQuantity: number;
	totalSellQuantity: number;
	netQuantity: number;
}

export interface AccountSummary {
	statistics: AccountStatistics;
}

export const emptyAccountStatistics: AccountStatistics = {
	totalTrades: 0,
	settledTrades: 0,
	pendingTrades: 0,
	totalBuyQuantity: 0,
	totalSellQuantity: 0,
	netQuantity: 0,
};