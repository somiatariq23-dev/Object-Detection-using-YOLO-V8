import React from 'react';
import { BarChart3, User, Car, Truck, Bus, Bike, Info } from 'lucide-react';

export default function AnalyticsPanel({ statistics }) {
  const current = statistics?.current || { person: 0, car: 0, bus: 0, truck: 0, bike: 0 };
  const cumulative = statistics?.cumulative || { person: 0, car: 0, bus: 0, truck: 0, bike: 0 };

  const targetClasses = [
    { key: 'person', label: 'Persons', icon: User, color: 'border-emerald-500/20 text-emerald-400 bg-emerald-500/5' },
    { key: 'car', label: 'Cars', icon: Car, color: 'border-blue-500/20 text-blue-400 bg-blue-500/5' },
    { key: 'bus', label: 'Buses', icon: Bus, color: 'border-yellow-500/20 text-yellow-400 bg-yellow-500/5' },
    { key: 'truck', label: 'Trucks', icon: Truck, color: 'border-orange-500/20 text-orange-400 bg-orange-500/5' },
    { key: 'bike', label: 'Bikes', icon: Bike, color: 'border-purple-500/20 text-purple-400 bg-purple-500/5' }
  ];

  // Compute total objects seen
  const totalCumulative = Object.values(cumulative).reduce((a, b) => a + b, 0);

  return (
    <div className="bg-glass rounded-2xl p-6 shadow-xl flex flex-col gap-6 h-full">
      <div className="flex justify-between items-center">
        <div className="flex items-center gap-2">
          <BarChart3 className="w-5 h-5 text-brand-blue" />
          <h2 className="text-lg font-bold text-slate-100">Detections Analytics</h2>
        </div>
        
        <div className="text-[10px] bg-slate-900 border border-slate-800 text-slate-400 px-3 py-1 rounded-full font-bold">
          TOTAL SEEN: {totalCumulative}
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        {targetClasses.map((item) => {
          const Icon = item.icon;
          const liveVal = current[item.key] || 0;
          const cumVal = cumulative[item.key] || 0;

          return (
            <div 
              key={item.key} 
              className={`border rounded-2xl p-4 flex flex-col justify-between gap-3 ${item.color}`}
            >
              {/* Header */}
              <div className="flex justify-between items-start">
                <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400">{item.label}</span>
                <Icon className="w-5 h-5" />
              </div>

              {/* Counts */}
              <div className="flex flex-col">
                <span className="text-3xl font-extrabold text-slate-100 Outfit tracking-tight">
                  {cumVal}
                </span>
                <div className="flex items-center justify-between mt-1 text-[10px]">
                  <span className="text-slate-500 font-semibold">Cumulative</span>
                  {liveVal > 0 ? (
                    <span className="bg-brand-green/10 text-brand-green border border-brand-green/15 px-1.5 py-0.5 rounded font-bold">
                      {liveVal} Live
                    </span>
                  ) : (
                    <span className="text-slate-500 font-mono">0 Live</span>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Analytics Insights */}
      <div className="mt-2 bg-slate-900/40 border border-slate-900 rounded-xl p-4 flex gap-3 text-xs text-slate-400 items-start">
        <Info className="w-5 h-5 text-brand-blue shrink-0 mt-0.5" />
        <div>
          <p className="font-bold text-slate-300">Tracking Optimization</p>
          <p className="mt-0.5 leading-relaxed text-[11px]">
            The unique cumulative counts are tracked across video frames using a Kalman-Filter based Hungarian algorithm. 
            This resolves object identities and prevents double counting when targets temporarily leave the screen or are occluded.
          </p>
        </div>
      </div>
    </div>
  );
}
