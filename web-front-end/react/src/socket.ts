import { io, Socket } from 'socket.io-client';
import { Environment } from './env';

const URL = process.env.NODE_ENV === 'production' ? undefined : Environment.trade_feed_url;

function createSocket(): Socket {
  const socketUrl = URL || '';
  return io(socketUrl, {
    forceNew: true,
  });
}

export const socket: Socket = createSocket();
