import React from 'react';
import { Eye, Shield, Cpu, Activity } from 'lucide-react';

export default function Navbar({ health }) {
  const isHealthy = health?.status === 'healthy';
  const device = health?.device || 'Unknown';
  const gpuName = health?.gpu_name;

  return (
    <header className="w-full bg-glass border-b border-slate-800 py-4 px-6 md:px-12 flex justify-between items-center z-50 sticky top-0">
      <div className="flex items-center gap-3">
        <div className="bg-gradient-to-tr from-brand-blue to-brand-green p-2 rounded-xl text-dark-900 shadow-md animate-pulse">
          <Eye className="w-6 h-6 stroke-[2.5]" />
        </div>
        <div>
          <h1 className="text-xl md:text-2xl font-extrabold tracking-tight bg-gradient-to-r from-white via-slate-100 to-slate-400 bg-clip-text text-transparent">
            EyeSight AI
          </h1>
          <p className="text-[10px] uppercase tracking-wider text-slate-500 font-bold -mt-1">
            Multi-Source Object Detection
          </p>
        </div>
      </div>

      <div className="flex items-center gap-4 text-xs">
        {/* Device Status */}
        <div className="hidden sm:flex items-center gap-2 bg-slate-900/60 border border-slate-800 rounded-lg px-3 py-1.5 text-slate-400">
          <Cpu className="w-4 h-4 text-brand-blue" />
          <span>Device: </span>
          <span className="font-semibold text-slate-200">
            {device.toUpperCase()} {gpuName ? `(${gpuName})` : ''}
          </span>
        </div>

        {/* Server Health Status */}
        <div className="flex items-center gap-2 bg-slate-900/60 border border-slate-800 rounded-lg px-3 py-1.5">
          <span className={`w-2.5 h-2.5 rounded-full ${isHealthy ? 'bg-brand-green animate-ping' : 'bg-red-500'}`} />
          <span className="text-slate-400">Server: </span>
          <span className={`font-semibold ${isHealthy ? 'text-brand-green' : 'text-red-500'}`}>
            {isHealthy ? 'ONLINE' : 'OFFLINE'}
          </span>
        </div>
      </div>
    </header>
  );
}
