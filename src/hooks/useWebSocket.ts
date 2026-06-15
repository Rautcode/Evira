// Frontend WebSocket client utilities.

import { useEffect, useRef, useState } from 'react';

interface WebSocketOptions {
  onMessage?: (data: any) => void;
  onError?: (error: Event) => void;
  onClose?: () => void;
  onOpen?: () => void;
}

export function useWebSocket(url: string, options: WebSocketOptions) {
  const ws = useRef<WebSocket | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Format WebSocket URL
    const wsUrl = url.startsWith('ws://') || url.startsWith('wss://')
      ? url
      : `ws://${window.location.host}${url.startsWith('/') ? '' : '/'}${url}`;

    // Create WebSocket connection
    ws.current = new WebSocket(wsUrl);

    // Connection opened
    ws.current.onopen = () => {
      setIsConnected(true);
      setError(null);
      options.onOpen?.();
    };

    // Listen for messages
    ws.current.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        options.onMessage?.(data);
      } catch (err) {
        console.error('Failed to parse WebSocket message:', err);
      }
    };

    // Handle errors
    ws.current.onerror = (event) => {
      setError('WebSocket error occurred');
      options.onError?.(event);
    };

    // Connection closed
    ws.current.onclose = () => {
      setIsConnected(false);
      setError('WebSocket connection closed');
      options.onClose?.();
    };

    // Cleanup on unmount
    return () => {
      ws.current?.close();
    };
  }, [url]);

  // Send message function
  const sendMessage = (data: any) => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify(data));
    } else {
      console.error('WebSocket is not connected');
    }
  };

  return {
    isConnected,
    error,
    sendMessage,
  };
}
