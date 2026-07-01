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