import React from 'react';
import { Sliders, ToggleLeft, ToggleRight, Eye } from 'lucide-react';

export default function ControlPanel({ 
  options, 
  onChange,
  disabled
}) {
  const handleToggle = (key) => {
    if (disabled) return;
    onChange({
      ...options,
      [key]: !options[key]
    });
  };

  const handleSliderChange = (e) => {
    if (disabled) return;
    onChange({
      ...options,
      conf_threshold: parseFloat(e.target.value)
    });
  };

  return (
    <div className="bg-glass rounded-2xl p-6 shadow-xl flex flex-col gap-6">
      <div className="flex items-center gap-2">
        <Sliders className="w-5 h-5 text-brand-blue" />
        <h2 className="text-lg font-bold text-slate-100 font-sans">Pipeline Control Panel</h2>
      </div>

      <div className="flex flex-col gap-5">
        {/* Conf Threshold Slider */}
        <div className="flex flex-col gap-2">
          <div className="flex justify-between items-center text-xs">
            <span className="font-bold text-slate-400 uppercase tracking-wider">Confidence Threshold</span>
            <span className="font-mono bg-slate-900 px-2 py-0.5 rounded text-brand-blue font-bold">
              {Math.round(options.conf_threshold * 100)}%
            </span>
          </div>
          <input
            type="range"
            min="0.05"
            max="0.95"
            step="0.05"
            value={options.conf_threshold}
            onChange={handleSliderChange}
            disabled={disabled}
            className="w-full accent-brand-blue bg-slate-800 rounded-lg appearance-none h-1.5 cursor-pointer disabled:cursor-not-allowed disabled:opacity-50"
          />
          <span className="text-[10px] text-slate-500">Filters out detections with lower confidence than this threshold.</span>
        </div>

        <div className="h-px bg-slate-800" />

        {/* Toggle Options */}
        <div className="flex flex-col gap-4">
          {/* Tracking */}
          <div className="flex justify-between items-center">
            <div>
              <p className="text-xs font-bold text-slate-200">Deep Tracking (SORT)</p>
              <p className="text-[10px] text-slate-500">Maintains object identities across frames</p>
            </div>
            <button
              onClick={() => handleToggle('draw_tracking')}
              disabled={disabled}
              className={`transition-colors duration-200 outline-none focus:outline-none ${
                disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'
              }`}
            >
              {options.draw_tracking ? (
                <ToggleRight className="w-10 h-10 text-brand-green fill-brand-green/10" />
              ) : (
                <ToggleLeft className="w-10 h-10 text-slate-600" />
              )}
            </button>
          </div>

          {/* Heatmap */}
          <div className="flex justify-between items-center">
            <div>
              <p className="text-xs font-bold text-slate-200">Density Heatmap</p>
              <p className="text-[10px] text-slate-500">Renders spatial object accumulation overlay</p>
            </div>
            <button
              onClick={() => handleToggle('draw_heatmap')}
              disabled={disabled}
              className={`transition-colors duration-200 outline-none focus:outline-none ${
                disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'
              }`}
            >
              {options.draw_heatmap ? (
                <ToggleRight className="w-10 h-10 text-brand-green fill-brand-green/10" />
              ) : (
                <ToggleLeft className="w-10 h-10 text-slate-600" />
              )}
            </button>
          </div>

          {/* HUD Overlay */}
          <div className="flex justify-between items-center">
            <div>
              <p className="text-xs font-bold text-slate-200">Video HUD Dashboard</p>
              <p className="text-[10px] text-slate-500">Draws semi-transparent statistics panel directly on video</p>
            </div>
            <button
              onClick={() => handleToggle('draw_hud')}
              disabled={disabled}
              className={`transition-colors duration-200 outline-none focus:outline-none ${
                disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'
              }`}
            >
              {options.draw_hud ? (
                <ToggleRight className="w-10 h-10 text-brand-green fill-brand-green/10" />
              ) : (
                <ToggleLeft className="w-10 h-10 text-slate-600" />
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
