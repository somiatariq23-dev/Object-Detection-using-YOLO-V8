import React, { useState } from 'react';
import { Video, Radio, Camera, Upload, Play, AlertCircle } from 'lucide-react';
import axios from 'axios';

export default function SourceSelector({ 
  onStreamStarted, 
  onUploadJobStarted,
  backendUrl,
  streamOptions
}) {
  const [activeTab, setActiveTab] = useState('upload'); // 'upload' | 'webcam' | 'rtsp'
  
  // Form states
  const [webcamIndex, setWebcamIndex] = useState('0');
  const [rtspUrl, setRtspUrl] = useState('rtsp://wowzaec2demo.streamlock.net/vod/mp4:BigBuckBunny_115k.mov');
  
  // File upload state
  const [file, setFile] = useState(null);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState('');

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    setError('');
    
    if (!selectedFile) return;
    
    // Check extension
    const ext = selectedFile.name.split('.').pop().toLowerCase();
    const allowed = ['mp4', 'avi', 'mov'];
    if (!allowed.includes(ext)) {
      setError(`Unsupported file type. Allowed formats: ${allowed.join(', ')}`);
      return;
    }

    // Check size (100MB limit)
    if (selectedFile.size > 100 * 1024 * 1024) {
      setError('File size exceeds the 100MB limit.');
      return;
    }

    setFile(selectedFile);
  };

  const handleUploadSubmit = async (e) => {
    e.preventDefault();
    if (!file) {
      setError('Please select a video file.');
      return;
    }

    setUploading(true);
    setError('');
    setUploadProgress(0);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await axios.post(`${backendUrl}/api/v1/video/upload`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        onUploadProgress: (progressEvent) => {
          const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          setUploadProgress(progress);
        },
      });

      const { stream_id, filename } = response.data;
      // Uploaded file is now a live stream session — same path as webcam/RTSP
      onStreamStarted(stream_id, filename);
      setFile(null);
      setUploadProgress(0);
    } catch (err) {
      setError(err.response?.data?.detail || 'Error uploading file.');
      console.error(err);
    } finally {
      setUploading(false);
    }
  };

  const handleStartStream = async (source) => {
    setError('');
    try {
      const response = await axios.post(`${backendUrl}/api/v1/stream/start`, {
        source: String(source),
        options: streamOptions
      });
      const { stream_id } = response.data;
      onStreamStarted(stream_id, source);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to start stream.');
      console.error(err);
    }
  };

  return (
    <div className="bg-glass rounded-2xl p-6 shadow-xl flex flex-col gap-6">
      <div>
        <h2 className="text-lg font-bold text-slate-100">Video Input Source</h2>
        <p className="text-xs text-slate-400">Select how you want to feed video into the analytics engine</p>
      </div>

      {/* Tabs Menu */}
      <div className="grid grid-cols-3 gap-2 bg-slate-900/60 p-1 rounded-xl border border-slate-800">
        <button
          onClick={() => { setActiveTab('upload'); setError(''); }}
          className={`flex items-center justify-center gap-2 py-2.5 rounded-lg text-xs font-semibold transition-all ${
            activeTab === 'upload' 
              ? 'bg-slate-800 text-white shadow-sm' 
              : 'text-slate-400 hover:text-slate-200'
          }`}
        >
          <Upload className="w-4 h-4" />
          <span>Upload File</span>
        </button>
        <button
          onClick={() => { setActiveTab('webcam'); setError(''); }}
          className={`flex items-center justify-center gap-2 py-2.5 rounded-lg text-xs font-semibold transition-all ${
            activeTab === 'webcam' 
              ? 'bg-slate-800 text-white shadow-sm' 
              : 'text-slate-400 hover:text-slate-200'
          }`}
        >
          <Camera className="w-4 h-4" />
          <span>Webcam</span>
        </button>
        <button
          onClick={() => { setActiveTab('rtsp'); setError(''); }}
          className={`flex items-center justify-center gap-2 py-2.5 rounded-lg text-xs font-semibold transition-all ${
            activeTab === 'rtsp' 
              ? 'bg-slate-800 text-white shadow-sm' 
              : 'text-slate-400 hover:text-slate-200'
          }`}
        >
          <Radio className="w-4 h-4" />
          <span>RTSP Feed</span>
        </button>
      </div>

      {/* Error Message */}
      {error && (
        <div className="bg-red-500/10 border border-red-500/20 text-red-400 text-xs rounded-xl p-3 flex items-start gap-2.5">
          <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
          <span>{error}</span>
        </div>
      )}

      {/* Tab Panels */}
      <div className="mt-2">
        {/* Local File Upload */}
        {activeTab === 'upload' && (
          <form onSubmit={handleUploadSubmit} className="flex flex-col gap-4">
            <div className="border-2 border-dashed border-slate-800 hover:border-slate-700 transition-all rounded-xl p-6 text-center cursor-pointer relative">
              <input
                type="file"
                accept=".mp4,.avi,.mov"
                onChange={handleFileChange}
                className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                disabled={uploading}
              />
              <Video className="w-8 h-8 text-slate-500 mx-auto mb-3" />
              {file ? (
                <div>
                  <p className="text-sm font-semibold text-slate-200 truncate">{file.name}</p>
                  <p className="text-[11px] text-slate-500 mt-1">{(file.size / (1024 * 1024)).toFixed(2)} MB</p>
                </div>
              ) : (
                <div>
                  <p className="text-xs font-semibold text-slate-300">Drag & drop your video file here</p>
                  <p className="text-[10px] text-slate-500 mt-1">Supports MP4, AVI, MOV up to 100MB</p>
                </div>
              )}
            </div>

            {uploading && (
              <div className="w-full bg-slate-900 border border-slate-800 rounded-lg p-3">
                <div className="flex justify-between items-center text-[10px] text-slate-400 font-bold mb-1">
                  <span>UPLOADING VIDEO...</span>
                  <span>{uploadProgress}%</span>
                </div>
                <div className="w-full bg-slate-800 rounded-full h-2 overflow-hidden">
                  <div 
                    className="bg-brand-blue h-full transition-all duration-300" 
                    style={{ width: `${uploadProgress}%` }}
                  />
                </div>
              </div>
            )}

            <button
              type="submit"
              disabled={uploading || !file}
              className={`w-full py-2.5 rounded-xl text-xs font-bold transition-all flex items-center justify-center gap-2 ${
                file && !uploading
                  ? 'bg-brand-blue text-white hover:bg-brand-blue/90 shadow-md shadow-brand-blue/15'
                  : 'bg-slate-800 text-slate-500 cursor-not-allowed'
              }`}
            >
              <Upload className="w-4 h-4" />
              <span>Upload and Process</span>
            </button>
          </form>
        )}

        {/* Webcam */}
        {activeTab === 'webcam' && (
          <div className="flex flex-col gap-4">
            <div className="flex flex-col gap-2">
              <label className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">Webcam Device Index</label>
              <input
                type="text"
                value={webcamIndex}
                onChange={(e) => setWebcamIndex(e.target.value)}
                placeholder="0"
                className="w-full bg-slate-900/60 border border-slate-800 focus:border-slate-700 outline-none rounded-xl px-4 py-2.5 text-sm text-slate-200"
              />
            </div>
            
            <button
              onClick={() => handleStartStream(webcamIndex)}
              className="w-full py-2.5 rounded-xl bg-brand-green hover:bg-brand-green/90 text-dark-900 text-xs font-bold transition-all flex items-center justify-center gap-2 shadow-md shadow-brand-green/15"
            >
              <Play className="w-4 h-4 fill-dark-900 text-dark-900" />
              <span>Start Webcam Feed</span>
            </button>
          </div>
        )}

        {/* RTSP Stream */}
        {activeTab === 'rtsp' && (
          <div className="flex flex-col gap-4">
            <div className="flex flex-col gap-2">
              <label className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">RTSP/Network Stream URL</label>
              <input
                type="text"
                value={rtspUrl}
                onChange={(e) => setRtspUrl(e.target.value)}
                placeholder="rtsp://host:port/stream"
                className="w-full bg-slate-900/60 border border-slate-800 focus:border-slate-700 outline-none rounded-xl px-4 py-2.5 text-xs text-slate-200 font-mono"
              />
            </div>
            
            <button
              onClick={() => handleStartStream(rtspUrl)}
              className="w-full py-2.5 rounded-xl bg-brand-green hover:bg-brand-green/90 text-dark-900 text-xs font-bold transition-all flex items-center justify-center gap-2 shadow-md shadow-brand-green/15"
            >
              <Play className="w-4 h-4 fill-dark-900 text-dark-900" />
              <span>Connect Live Feed</span>
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
