import React, { useState, useEffect } from 'react';
import Navbar from './components/Navbar';
import SourceSelector from './components/SourceSelector';
import VideoPlayer from './components/VideoPlayer';
import ControlPanel from './components/ControlPanel';
import AnalyticsPanel from './components/AnalyticsPanel';
import axios from 'axios';

// Resolve Backend Server URL (Assumed on Port 8000 on same host or localhost)
const BACKEND_URL = window.location.origin.includes('localhost') || window.location.origin.includes('127.0.0.1')
  ? 'http://127.0.0.1:8000'
  : `${window.location.protocol}//${window.location.hostname}:8000`;

export default function App() {
  const [health, setHealth] = useState(null);
  
  // Active session states
  const [streamId, setStreamId] = useState(null);
  const [sourceName, setSourceName] = useState(null);
  
  // Real-time statistics
  const [statistics, setStatistics] = useState({
    current: { person: 0, car: 0, bus: 0, truck: 0, bike: 0 },
    cumulative: { person: 0, car: 0, bus: 0, truck: 0, bike: 0 }
  });

  // Global settings options
  const [options, setOptions] = useState({
    draw_tracking: true,
    draw_heatmap: false,
    draw_hud: true,
    conf_threshold: 0.25
  });

  // 1. Fetch Server Health on Mount
  useEffect(() => {
    const fetchHealth = async () => {
      try {
        const res = await axios.get(`${BACKEND_URL}/api/v1/health`);
        setHealth(res.data);
      } catch (err) {
        console.error("Error checking server health:", err);
      }
    };

    fetchHealth();
    const interval = setInterval(fetchHealth, 5000);
    return () => clearInterval(interval);
  }, []);

  // 2. Poll Active Stream Status (for object counts statistics)
  useEffect(() => {
    if (!streamId) return;

    const fetchStreamStatus = async () => {
      try {
        const res = await axios.get(`${BACKEND_URL}/api/v1/stream/status/${streamId}`);
        const data = res.data;
        if (data.statistics) setStatistics(data.statistics);
        if (data.status === 'stopped' || data.status === 'failed') {
          setStreamId(null);
          setSourceName(null);
        }
      } catch (err) {
        console.error("Error fetching stream status:", err);
        setStreamId(null);
        setSourceName(null);
      }
    };

    const interval = setInterval(fetchStreamStatus, 1000);
    return () => clearInterval(interval);
  }, [streamId]);

  const handleStreamStarted = (id, source) => {
    setStreamId(id);
    setSourceName(source);
    setStatistics({
      current: { person: 0, car: 0, bus: 0, truck: 0, bike: 0 },
      cumulative: { person: 0, car: 0, bus: 0, truck: 0, bike: 0 }
    });
  };

  const handleStopSession = async () => {
    if (streamId) {
      try {
        await axios.post(`${BACKEND_URL}/api/v1/stream/stop/${streamId}`);
      } catch (err) {
        console.error("Error stopping stream:", err);
      }
      setStreamId(null);
      setSourceName(null);
    }
  };

  return (
    <div className="relative min-h-screen bg-dark-900 text-slate-100 flex flex-col font-sans">
      
      {/* Visual Design Background Blobs */}
      <div className="absolute top-[-10%] left-[-10%] w-[50%] aspect-square rounded-full bg-brand-blue/5 blur-[120px] pointer-events-none" />
      <div className="absolute bottom-[-10%] right-[-10%] w-[50%] aspect-square rounded-full bg-brand-green/5 blur-[120px] pointer-events-none" />
      
      <Navbar health={health} />
      
      <main className="flex-1 w-full max-w-7xl mx-auto p-6 md:p-10 flex flex-col gap-6">
        
        {/* Main Grid Section */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
          
          {/* Controls & Inputs (Left) */}
          <div className="lg:col-span-4 flex flex-col gap-6 w-full">
            <SourceSelector 
              onStreamStarted={handleStreamStarted}
              backendUrl={BACKEND_URL}
              streamOptions={options}
            />
            
            <ControlPanel 
              options={options} 
              onChange={setOptions}
              disabled={streamId !== null}
            />
          </div>
          
          {/* Video Player Display (Right) */}
          <div className="lg:col-span-8 w-full flex flex-col h-full">
            <VideoPlayer
              streamId={streamId}
              onStopClick={handleStopSession}
              backendUrl={BACKEND_URL}
              sourceName={sourceName}
            />
          </div>
          
        </div>

        {/* Analytics Display (Bottom) */}
        <div className="w-full">
          <AnalyticsPanel statistics={statistics} />
        </div>
        
      </main>
      
      <footer className="py-6 border-t border-slate-900 text-center text-xs text-slate-600">
        &copy; {new Date().getFullYear()} EyeSight Multi-Source Video Analytics System. Powered by FastAPI & YOLOv8.
      </footer>
    </div>
  );
}
