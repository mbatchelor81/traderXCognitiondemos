import { io, Socket } from 'socket.io-client';
import { Environment } from './env';
import { getCurrentTenant } from './fetchWithTenant';

const URL = process.env.NODE_ENV === 'production' ? undefined : Environment.trade_feed_url;

function createSocket(tenant: string): Socket {
  const socketUrl = URL || '';
  return io(socketUrl, {
    query: { tenant },
    forceNew: true,
  });
}

export let socket = createSocket(getCurrentTenant());

/**
 * Reconnect the socket with a new tenant.
 * Disconnects the old socket and creates a new one.
 */
export function reconnectSocket(tenant: string): Socket {
  socket.disconnect();
  socket = createSocket(tenant);
  return socket;
}
