import React, { useEffect, useState, useRef } from 'react';
import { CameraOff, RefreshCw } from 'lucide-react';

export default function VideoPlayer({ streamId, onStopClick, backendUrl, sourceName }) {
  const [imageSrc, setImageSrc] = useState(null);
  const [connectionStatus, setConnectionStatus] = useState('disconnected');
  const wsRef = useRef(null);
  const prevUrlRef = useRef(null);

  useEffect(() => {
    const cleanup = () => {
      if (wsRef.current) { wsRef.current.close(); wsRef.current = null; }
      if (prevUrlRef.current) { URL.revokeObjectURL(prevUrlRef.current); prevUrlRef.current = null; }
      setImageSrc(null);
      setConnectionStatus('disconnected');
    };

    cleanup();
    if (!streamId) return;

    setConnectionStatus('connecting');
    const wsUrl = `${backendUrl.replace(/^http/, 'ws')}/ws/stream/${streamId}`;
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;
    ws.binaryType = 'blob';

    ws.onopen = () => setConnectionStatus('connected');
    ws.onmessage = (event) => {
      if (event.data instanceof Blob) {
        const newUrl = URL.createObjectURL(event.data);
        setImageSrc(newUrl);
        if (prevUrlRef.current) URL.revokeObjectURL(prevUrlRef.current);
        prevUrlRef.current = newUrl;
      }
    };
    ws.onerror = () => setConnectionStatus('error');
    ws.onclose = () => setConnectionStatus('disconnected');

    return cleanup;
  }, [streamId, backendUrl]);

  return (
    <div className="bg-glass rounded-2xl p-6 shadow-xl flex flex-col gap-4 flex-1">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-lg font-bold text-slate-100">Live Video Monitor</h2>
          {streamId ? (
            <p className="text-xs text-brand-green flex items-center gap-1.5 font-semibold">
              <span className="w-2 h-2 bg-brand-green rounded-full animate-ping" />
              <span>LIVE: {String(sourceName).toUpperCase()}</span>
            </p>
          ) : (
            <p className="text-xs text-slate-500 font-semibold uppercase">SYSTEM IDLE</p>
          )}
        </div>
        {streamId && (
          <button
            onClick={onStopClick}
            className="px-4 py-1.5 rounded-lg bg-red-500/10 hover:bg-red-500/20 text-red-400 border border-red-500/20 hover:border-red-500/30 text-xs font-bold transition-all"
          >
            Stop Session
          </button>
        )}
      </div>

      <div className="relative aspect-video w-full bg-slate-950 border border-slate-900 rounded-xl overflow-hidden flex items-center justify-center">
        {streamId && imageSrc && (
          <img src={imageSrc} alt="Live Feed" className="w-full h-full object-contain" />
        )}
        {streamId && !imageSrc && (
          <div className="flex flex-col items-center gap-3">
            <RefreshCw className="w-8 h-8 text-brand-blue animate-spin" />
            <p className="text-xs text-slate-400 font-semibold tracking-wider">
              {connectionStatus === 'connecting' ? 'INITIALIZING STREAM...' : 'WAITING FOR FRAMES...'}
            </p>
          </div>
        )}
        {!streamId && (
          <div className="flex flex-col items-center gap-3">
            <CameraOff className="w-10 h-10 text-slate-600" />
            <p className="text-xs text-slate-500 font-semibold tracking-wider uppercase">No Active Video Source</p>
          </div>
        )}
      </div>

      {streamId && (
        <div className="flex items-center gap-4 bg-slate-900/40 border border-slate-900 rounded-xl px-4 py-2.5 text-xs text-slate-400">
          <span>Status: <span className={`font-semibold uppercase ${
            connectionStatus === 'connected' ? 'text-brand-green' : 'text-slate-500'
          }`}>{connectionStatus}</span></span>
          <div className="h-4 w-px bg-slate-800" />
          <span>Source: <span className="font-semibold text-slate-300">{sourceName}</span></span>
        </div>
      )}
    </div>
  );
}
