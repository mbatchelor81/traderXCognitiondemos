import { io, Socket } from 'socket.io-client';
import { Environment, TENANT_ID } from './env';

const URL = process.env.NODE_ENV === 'production' ? undefined : Environment.trade_feed_url;

/**
 * Single socket connection — tenant is fixed at build time.
 * No reconnect-on-tenant-switch needed in single-tenant mode.
 */
export const socket: Socket = io(URL || '', {
  query: { tenant: TENANT_ID },
});
