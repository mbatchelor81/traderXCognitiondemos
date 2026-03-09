import { io, Socket } from 'socket.io-client';
import { Environment, TENANT_ID } from './env';

const URL = process.env.NODE_ENV === 'production' ? undefined : Environment.trade_feed_url;

const socketUrl = URL || '';
export const socket: Socket = io(socketUrl, {
  query: { tenant: TENANT_ID },
});
