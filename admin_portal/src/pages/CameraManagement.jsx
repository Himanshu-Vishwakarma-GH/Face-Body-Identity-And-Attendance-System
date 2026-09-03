import React, { useState, useEffect } from 'react';
import { api } from '../api';
import { Camera, Radio, Link2, Unlink, RefreshCw, Plus, CheckCircle2 } from 'lucide-react';

export default function CameraManagement() {
  const [cameras, setCameras] = useState([]);
  const [discovered, setDiscovered] = useState([]);
  const [loading, setLoading] = useState(true);
  const [scanning, setScanning] = useState(false);
  const [actionMsg, setActionMsg] = useState('');

  const fetchCameras = async () => {
    setLoading(true);
    try {
      const data = await api.getCameras();
      setCameras(data);
    } catch (err) {
      console.error('Failed to load cameras:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCameras();
  }, []);

  const handleScan = async () => {
    setScanning(true);
    setActionMsg('');
    try {
      const results = await api.scanCameras();
      setDiscovered(results);
      if (results.length === 0) {
        setActionMsg('No new unlinked network cameras discovered.');
      } else {
        setActionMsg(`Found ${results.length} available network cameras ready to link.`);
      }
    } catch (err) {
      alert('Network scan failed: ' + err.message);
    } finally {
      setScanning(false);
    }
  };

  const handleLink = async (camId, zone = '') => {
    try {
      await api.linkCamera(camId, zone);
      setActionMsg(`Camera ${camId} successfully linked into security perimeter!`);
      // Remove from discovered list
      setDiscovered((prev) => prev.filter((c) => c.camera_id !== camId));
      fetchCameras();
    } catch (err) {
      alert('Failed to link camera: ' + err.message);
    }
  };

  const handleUnlink = async (camId) => {
    try {
      await api.unlinkCamera(camId);
      setActionMsg(`Camera ${camId} dynamically unlinked.`);
      fetchCameras();
    } catch (err) {
      alert('Failed to unlink camera: ' + err.message);
    }
  };

  const handleRelink = async (camId) => {
    try {
      await api.relinkCamera(camId);
      setActionMsg(`Camera ${camId} relinked.`);
      fetchCameras();
    } catch (err) {
      alert('Failed to relink camera: ' + err.message);
    }
  };

  return (
    <div className="space-y-8">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-white tracking-tight">Dynamic Camera Management</h2>
          <p className="text-sm text-gray-400 mt-1">
            Auto-scan network and link/unlink ONVIF &amp; RTSP cameras on the fly with zero backend restarts.
          </p>
        </div>

        <button
          onClick={handleScan}
          disabled={scanning}
          className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-sm font-semibold text-white shadow-lg shadow-blue-600/20 transition-all disabled:opacity-50"
        >
          <Radio className={`w-4 h-4 ${scanning ? 'animate-pulse' : ''}`} />
          <span>{scanning ? 'Scanning Network...' : 'Auto-Scan Network (ONVIF)'}</span>
        </button>
      </div>

      {actionMsg && (
        <div className="p-4 rounded-xl bg-blue-500/10 border border-blue-500/20 text-blue-400 text-sm flex items-center gap-2">
          <CheckCircle2 className="w-5 h-5 shrink-0" />
          <span>{actionMsg}</span>
        </div>
      )}

      {/* Discovered Cameras Available to Link */}
      {discovered.length > 0 && (
        <div className="bg-dark-800 border border-blue-500/30 p-6 rounded-2xl space-y-4">
          <div className="flex items-center gap-2 text-blue-400 font-bold text-base">
            <Radio className="w-5 h-5 animate-pulse" />
            <span>Discovered Network Devices Ready to Link ({discovered.length})</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {discovered.map((cam) => (
              <div key={cam.camera_id} className="bg-dark-900 border border-dark-700 p-4 rounded-xl flex items-center justify-between">
                <div>
                  <div className="font-semibold text-white">{cam.name} ({cam.camera_id})</div>
                  <div className="text-xs text-gray-400">{cam.location} &bull; {cam.ip_address}</div>
                  <div className="text-xs text-blue-400 mt-1">Zone: {cam.zone}</div>
                </div>

                <button
                  onClick={() => handleLink(cam.camera_id, cam.zone)}
                  className="px-3.5 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold transition-colors flex items-center gap-1.5"
                >
                  <Plus className="w-4 h-4" />
                  <span>Link Camera</span>
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Linked Cameras Grid */}
      <div className="space-y-4">
        <h3 className="text-lg font-bold text-white">Currently Registered Cameras</h3>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {cameras.map((cam) => {
            const isLive = cam.is_linked && cam.status === 'ACTIVE';
            return (
              <div
                key={cam.camera_id}
                className={`bg-dark-800 border p-5 rounded-2xl flex flex-col justify-between transition-all ${
                  isLive ? 'border-dark-700' : 'border-red-500/30 opacity-75'
                }`}
              >
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-xs font-bold text-blue-400 bg-blue-500/10 px-2.5 py-1 rounded-md">
                      {cam.camera_id}
                    </span>
                    <span
                      className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold ${
                        isLive
                          ? 'bg-emerald-500/10 text-emerald-400'
                          : cam.status === 'UNLINKED'
                          ? 'bg-gray-800 text-gray-400'
                          : 'bg-red-500/10 text-red-400'
                      }`}
                    >
                      <span className={`w-1.5 h-1.5 rounded-full ${isLive ? 'bg-emerald-400' : 'bg-red-400'}`} />
                      {cam.status}
                    </span>
                  </div>

                  <div>
                    <h4 className="font-bold text-white text-base">{cam.name}</h4>
                    <p className="text-xs text-gray-400">{cam.location} &bull; {cam.floor}</p>
                  </div>

                  <div className="text-xs space-y-1 bg-dark-900/60 p-3 rounded-xl border border-dark-700/50">
                    <div className="text-gray-400 flex justify-between">
                      <span>Zone:</span>
                      <span className="font-medium text-gray-200">{cam.zone}</span>
                    </div>
                    <div className="text-gray-400 flex justify-between">
                      <span>IP Address:</span>
                      <span className="font-mono text-gray-300">{cam.ip_address}</span>
                    </div>
                    <div className="text-gray-400 flex justify-between">
                      <span>Stream:</span>
                      <span className="font-mono text-gray-400 truncate max-w-[140px]">{cam.rtsp_url}</span>
                    </div>
                  </div>
                </div>

                <div className="mt-5 pt-4 border-t border-dark-700/50 flex justify-end gap-2">
                  {cam.is_linked ? (
                    <button
                      onClick={() => handleUnlink(cam.camera_id)}
                      className="px-3 py-1.5 rounded-lg bg-dark-700 hover:bg-dark-600 text-xs font-medium text-gray-300 hover:text-white transition-colors flex items-center gap-1.5"
                    >
                      <Unlink className="w-3.5 h-3.5" />
                      <span>Unlink</span>
                    </button>
                  ) : (
                    <button
                      onClick={() => handleRelink(cam.camera_id)}
                      className="px-3 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-xs font-bold text-white transition-colors flex items-center gap-1.5"
                    >
                      <Link2 className="w-3.5 h-3.5" />
                      <span>Re-Link</span>
                    </button>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
