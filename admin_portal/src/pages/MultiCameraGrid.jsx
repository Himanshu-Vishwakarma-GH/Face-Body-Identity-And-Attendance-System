import React, { useState, useEffect } from 'react';
import { api } from '../api';
import {
  Camera,
  Smartphone,
  Video,
  Plus,
  Play,
  Maximize2,
  RefreshCw,
  CheckCircle2,
  AlertCircle,
  Radio,
  Eye,
  X,
  Wifi,
  Copy,
  ExternalLink,
  Cpu
} from 'lucide-react';

export default function MultiCameraGrid() {
  const [cameras, setCameras] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showWizard, setShowWizard] = useState(false);
  const [selectedFeed, setSelectedFeed] = useState(null);
  const [quickVerifyResult, setQuickVerifyResult] = useState(null);

  // Wizard form state
  const [wizardType, setWizardType] = useState('phone'); // 'phone' | 'usb' | 'rtsp'
  const [phoneMode, setPhoneMode] = useState('browser'); // 'browser' (no-app) | 'app' (IP Webcam)
  const [camId, setCamId] = useState('');
  const [camName, setCamName] = useState('');
  const [camLocation, setCamLocation] = useState('');
  const [camZone, setCamZone] = useState('Entry Zone A');
  const [sourceUrl, setSourceUrl] = useState('');
  const [testResult, setTestResult] = useState(null);
  const [testing, setTesting] = useState(false);
  const [saving, setSaving] = useState(false);
  const [zones, setZones] = useState([]);

  // Hardware auto-detection state
  const [detectedUsbCameras, setDetectedUsbCameras] = useState([]);
  const [detectingUsb, setDetectingUsb] = useState(false);
  const [detectedPhones, setDetectedPhones] = useState([]);
  const [scanningPhones, setScanningPhones] = useState(false);
  const [networkInfo, setNetworkInfo] = useState({ local_ip: '127.0.0.1', phone_cam_url: '', subnet: '192.168.1.0/24' });
  const [copiedLink, setCopiedLink] = useState(false);

  const scanWifiPhones = async () => {
    setScanningPhones(true);
    setTestResult(null);
    try {
      const phones = await api.scanWifiPhoneCameras();
      setDetectedPhones(phones);
      if (phones.length > 0) {
        setSourceUrl(phones[0].stream_url);
        setCamName(phones[0].suggested_name);
      }
    } catch (err) {
      console.error('Failed to scan for phone cameras:', err);
    } finally {
      setScanningPhones(false);
    }
  };

  const loadCameras = async () => {
    setLoading(true);
    try {
      const [cams, zList, netInfo] = await Promise.all([
        api.getCameras(false),
        api.getZones().catch(() => []),
        api.getNetworkInfo().catch(() => ({ local_ip: '127.0.0.1' }))
      ]);
      setCameras(cams);
      setNetworkInfo(netInfo);
      if (zList.length > 0) {
        setZones(zList);
        setCamZone(zList[0].name);
      }
    } catch (err) {
      console.error('Failed to load cameras:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadCameras();
    const interval = setInterval(loadCameras, 15000);
    return () => clearInterval(interval);
  }, []);

  // Auto-scan USB cameras on demand
  const scanUsbCameras = async () => {
    setDetectingUsb(true);
    try {
      const devs = await api.detectUsbCameras();
      setDetectedUsbCameras(devs);
      if (devs.length > 0 && wizardType === 'usb') {
        selectUsbCamera(devs[0].index, devs[0].name);
      }
    } catch (err) {
      console.error('Failed to detect USB cameras:', err);
    } finally {
      setDetectingUsb(false);
    }
  };

  // Select USB camera
  const selectUsbCamera = (index, name = '') => {
    setSourceUrl(String(index));
    setCamName(name || `USB Camera ${index}`);
    setTestResult(null);
  };

  // Switch Wizard Tab
  const handleTypeSelect = (type) => {
    setWizardType(type);
    setTestResult(null);

    const randId = Math.floor(100 + Math.random() * 900);
    if (type === 'usb') {
      const newId = `CAM-USB-${randId}`;
      setCamId(newId);
      setCamLocation('Local Workstation');
      setSourceUrl('0');
      scanUsbCameras();
    } else if (type === 'phone') {
      const newId = `CAM-PHONE-${randId}`;
      setCamId(newId);
      setCamName('Mobile Security Patrol');
      setCamLocation('Mobile Checkpoint');
      if (phoneMode === 'browser') {
        setSourceUrl(`phone:${newId}`);
      } else {
        const subnetBase = networkInfo.local_ip ? networkInfo.local_ip.substring(0, networkInfo.local_ip.lastIndexOf('.')) : '192.168.1';
        setSourceUrl(`http://${subnetBase}.50:8080/video`);
      }
    } else {
      setCamId(`CAM-NET-${randId}`);
      setCamName('Network CCTV Camera');
      setCamLocation('Hallway Perimeter');
      setSourceUrl('rtsp://admin:admin@192.168.1.100:554/live');
    }
  };

  // Switch Phone mode
  const handlePhoneModeSelect = (mode) => {
    setPhoneMode(mode);
    setTestResult(null);
    if (mode === 'browser') {
      setSourceUrl(`phone:${camId}`);
    } else {
      const subnetBase = networkInfo.local_ip ? networkInfo.local_ip.substring(0, networkInfo.local_ip.lastIndexOf('.')) : '192.168.1';
      setSourceUrl(`http://${subnetBase}.50:8080/video`);
    }
  };

  // Test Camera Source
  const handleTestSource = async () => {
    if (!sourceUrl) return;
    setTesting(true);
    setTestResult(null);
    try {
      const res = await api.testCameraSource(sourceUrl);
      setTestResult(res);
    } catch (err) {
      setTestResult({
        success: false,
        message: err.message || 'Failed to connect to camera source'
      });
    } finally {
      setTesting(false);
    }
  };

  // Save New Camera
  const handleSaveCamera = async (e) => {
    e.preventDefault();
    if (!camId || !camName || !sourceUrl) return;

    setSaving(true);
    try {
      await api.addCamera({
        camera_id: camId.trim().toUpperCase(),
        name: camName.trim(),
        location: camLocation.trim() || 'General Location',
        zone: camZone,
        rtsp_url: sourceUrl.trim(),
        is_linked: true,
        status: 'ACTIVE'
      });
      setShowWizard(false);
      setTestResult(null);
      await loadCameras();
    } catch (err) {
      alert(`Error saving camera: ${err.message}`);
    } finally {
      setSaving(false);
    }
  };

  // Quick Live AI Verification from camera stream
  const handleQuickVerify = async (cam) => {
    setQuickVerifyResult({ camId: cam.camera_id, verifying: true });
    try {
      const res = await api.verifyAccess({
        camera_id: cam.camera_id,
        employee_id: '' // Biometric 1:N identification
      });
      setQuickVerifyResult({
        camId: cam.camera_id,
        verifying: false,
        decision: res.decision,
        person: res.employee_name || 'Unidentified Person',
        faceScore: Math.round((res.face_confidence || 0) * 100),
        message: res.message
      });
      setTimeout(() => setQuickVerifyResult(null), 5000);
    } catch (err) {
      setQuickVerifyResult({
        camId: cam.camera_id,
        verifying: false,
        decision: 'ERROR',
        message: 'Could not contact camera sensor'
      });
      setTimeout(() => setQuickVerifyResult(null), 4000);
    }
  };

  const phoneBroadcastUrl = `http://${networkInfo.local_ip || '127.0.0.1'}:8000/phone-cam?id=${camId}`;

  const copyPhoneUrl = () => {
    navigator.clipboard.writeText(phoneBroadcastUrl);
    setCopiedLink(true);
    setTimeout(() => setCopiedLink(false), 2500);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <Radio className="w-5 h-5 text-emerald-400 animate-pulse" />
            <h2 className="text-2xl font-bold text-white tracking-tight">Multi-Camera Security Wall</h2>
          </div>
          <p className="text-sm text-gray-400 mt-1">
            Real-time surveillance matrix with direct USB hardware detection &amp; same-network Wi-Fi phone streaming.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => {
              setShowWizard(true);
              handleTypeSelect('usb');
            }}
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white text-sm font-semibold shadow-lg shadow-blue-600/25 transition-all"
          >
            <Plus className="w-4 h-4" />
            <span>Connect Camera</span>
          </button>

          <button
            onClick={loadCameras}
            className="p-2.5 rounded-xl bg-dark-800 border border-dark-700 hover:bg-dark-700 text-gray-300 transition-colors"
            title="Refresh feeds"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* CCTV Matrix Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {cameras.length === 0 ? (
          <div className="col-span-full bg-dark-800 border border-dark-700 rounded-2xl p-12 text-center space-y-4">
            <Camera className="w-12 h-12 text-gray-600 mx-auto" />
            <h3 className="text-lg font-bold text-white">No Cameras Connected Yet</h3>
            <p className="text-sm text-gray-400 max-w-md mx-auto">
              Pair your phone camera over Wi-Fi, laptop webcam, or USB camera with 1 click to begin monitoring checkpoints.
            </p>
            <button
              onClick={() => {
                setShowWizard(true);
                handleTypeSelect('usb');
              }}
              className="px-6 py-2.5 bg-blue-600 hover:bg-blue-500 text-white text-sm font-semibold rounded-xl"
            >
              Add Your First Camera
            </button>
          </div>
        ) : (
          cameras.map((cam) => {
            const isLive = cam.status === 'ACTIVE' && cam.is_linked;
            const verifyInfo = quickVerifyResult?.camId === cam.camera_id ? quickVerifyResult : null;

            return (
              <div
                key={cam.camera_id}
                className="bg-dark-800 border border-dark-700 rounded-2xl overflow-hidden flex flex-col group hover:border-dark-600 transition-all shadow-xl"
              >
                {/* Video Monitor Frame */}
                <div className="relative aspect-video bg-black flex items-center justify-center overflow-hidden">
                  {isLive ? (
                    <img
                      src={`/api/camera/${cam.camera_id}/stream`}
                      alt={cam.name}
                      className="w-full h-full object-cover"
                      onError={(e) => {
                        e.target.onerror = null;
                        e.target.src = `/api/camera/${cam.camera_id}/snapshot?t=${Date.now()}`;
                      }}
                    />
                  ) : (
                    <div className="text-center p-6 space-y-2">
                      <Camera className="w-10 h-10 text-gray-700 mx-auto" />
                      <div className="text-xs font-mono text-gray-500">FEED OFFLINE / UNLINKED</div>
                    </div>
                  )}

                  {/* Optical Reticle Frame Lines */}
                  <div className="absolute inset-2 border border-white/5 pointer-events-none rounded-lg">
                    <div className="absolute top-0 left-0 w-3 h-3 border-t-2 border-l-2 border-blue-500/60" />
                    <div className="absolute top-0 right-0 w-3 h-3 border-t-2 border-r-2 border-blue-500/60" />
                    <div className="absolute bottom-0 left-0 w-3 h-3 border-b-2 border-l-2 border-blue-500/60" />
                    <div className="absolute bottom-0 right-0 w-3 h-3 border-b-2 border-r-2 border-blue-500/60" />
                  </div>

                  {/* Live HUD Badges */}
                  <div className="absolute top-3 left-3 flex items-center gap-2">
                    <span
                      className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-bold ${
                        isLive ? 'bg-red-500/20 text-red-400 border border-red-500/30' : 'bg-gray-800 text-gray-400'
                      }`}
                    >
                      <span className={`w-2 h-2 rounded-full ${isLive ? 'bg-red-500 animate-ping' : 'bg-gray-500'}`} />
                      {isLive ? 'LIVE' : 'STANDBY'}
                    </span>
                    <span className="bg-black/60 backdrop-blur px-2 py-0.5 rounded text-xs font-mono text-gray-300">
                      {cam.camera_id}
                    </span>
                  </div>

                  <div className="absolute top-3 right-3">
                    <button
                      onClick={() => setSelectedFeed(cam)}
                      className="p-1.5 bg-black/60 hover:bg-black/80 backdrop-blur rounded-lg text-gray-300 hover:text-white transition-colors"
                      title="Fullscreen"
                    >
                      <Maximize2 className="w-3.5 h-3.5" />
                    </button>
                  </div>

                  {/* Quick AI Verification Result Overlay */}
                  {verifyInfo && (
                    <div className="absolute inset-0 bg-black/80 backdrop-blur-sm flex flex-col items-center justify-center p-4 text-center">
                      {verifyInfo.verifying ? (
                        <div className="space-y-2">
                          <RefreshCw className="w-8 h-8 text-blue-400 animate-spin mx-auto" />
                          <div className="text-xs font-bold text-blue-400 uppercase tracking-wider">
                            Analyzing Biometrics...
                          </div>
                        </div>
                      ) : (
                        <div className="space-y-1.5">
                          <span
                            className={`inline-block px-3 py-1 rounded-full text-xs font-extrabold ${
                              verifyInfo.decision === 'GRANTED'
                                ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/40'
                                : 'bg-red-500/20 text-red-400 border border-red-500/40'
                            }`}
                          >
                            {verifyInfo.decision}
                          </span>
                          <div className="font-bold text-white text-sm">{verifyInfo.person}</div>
                          {verifyInfo.faceScore > 0 && (
                            <div className="text-xs font-mono text-gray-400">Match: {verifyInfo.faceScore}%</div>
                          )}
                          <div className="text-xs text-gray-400 mt-1 max-w-[200px] truncate">{verifyInfo.message}</div>
                        </div>
                      )}
                    </div>
                  )}
                </div>

                {/* Camera Card Info */}
                <div className="p-4 flex flex-col justify-between flex-1 gap-3">
                  <div>
                    <div className="flex items-center justify-between">
                      <h4 className="font-bold text-white text-sm">{cam.name}</h4>
                      <span className="text-xs font-medium text-blue-400 bg-blue-500/10 px-2 py-0.5 rounded-md">
                        {cam.zone}
                      </span>
                    </div>
                    <div className="text-xs text-gray-400 mt-0.5">{cam.location}</div>
                  </div>

                  <div className="flex items-center justify-between pt-2 border-t border-dark-700">
                    <div className="text-[11px] font-mono text-gray-500 truncate max-w-[150px]">
                      SRC: {cam.rtsp_url}
                    </div>

                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => handleQuickVerify(cam)}
                        className="px-3 py-1.5 bg-dark-700 hover:bg-dark-600 text-gray-200 text-xs font-semibold rounded-lg flex items-center gap-1.5 transition-colors"
                        title="Identify person currently in front of this camera"
                      >
                        <Eye className="w-3 h-3 text-blue-400" />
                        <span>Identify</span>
                      </button>

                      {cam.is_linked ? (
                        <button
                          onClick={async () => {
                            await api.unlinkCamera(cam.camera_id);
                            loadCameras();
                          }}
                          className="px-2.5 py-1.5 bg-red-500/10 hover:bg-red-500/20 text-red-400 text-xs font-semibold rounded-lg transition-colors"
                        >
                          Unlink
                        </button>
                      ) : (
                        <button
                          onClick={async () => {
                            await api.linkCamera(cam.camera_id, cam.zone);
                            loadCameras();
                          }}
                          className="px-2.5 py-1.5 bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 text-xs font-semibold rounded-lg transition-colors"
                        >
                          Link
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>

      {/* Fullscreen Feed Modal */}
      {selectedFeed && (
        <div className="fixed inset-0 z-50 bg-black/90 backdrop-blur flex items-center justify-center p-6">
          <div className="bg-dark-900 border border-dark-700 rounded-2xl w-full max-w-5xl overflow-hidden flex flex-col">
            <div className="p-4 border-b border-dark-700 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <span className="w-2.5 h-2.5 rounded-full bg-red-500 animate-ping" />
                <span className="font-bold text-white">{selectedFeed.name}</span>
                <span className="text-xs font-mono text-gray-400">({selectedFeed.camera_id})</span>
              </div>
              <button
                onClick={() => setSelectedFeed(null)}
                className="p-1.5 hover:bg-dark-800 rounded-lg text-gray-400 hover:text-white"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="aspect-video bg-black flex items-center justify-center">
              <img
                src={`/api/camera/${selectedFeed.camera_id}/stream`}
                alt={selectedFeed.name}
                className="w-full h-full object-contain"
              />
            </div>
          </div>
        </div>
      )}

      {/* Easy Camera Connect Wizard Modal */}
      {showWizard && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-dark-800 border border-dark-700 rounded-3xl w-full max-w-2xl overflow-hidden shadow-2xl flex flex-col max-h-[90vh]">
            {/* Wizard Header */}
            <div className="p-6 border-b border-dark-700 flex items-center justify-between">
              <div>
                <h3 className="text-xl font-bold text-white tracking-tight">Connect Security Camera</h3>
                <p className="text-xs text-gray-400 mt-1">Plug-and-play setup for USB hardware or same Wi-Fi phone cameras.</p>
              </div>
              <button
                onClick={() => setShowWizard(false)}
                className="p-2 hover:bg-dark-700 rounded-xl text-gray-400 hover:text-white"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="overflow-y-auto p-6 space-y-5">
              {/* 3 Device Type Selector Tabs */}
              <div className="grid grid-cols-3 gap-3">
                <button
                  type="button"
                  onClick={() => handleTypeSelect('usb')}
                  className={`p-4 rounded-2xl border text-left flex flex-col gap-2 transition-all ${
                    wizardType === 'usb'
                      ? 'border-emerald-500 bg-emerald-500/10 text-white'
                      : 'border-dark-700 bg-dark-900/50 text-gray-400 hover:text-white hover:border-dark-600'
                  }`}
                >
                  <Camera className="w-6 h-6 text-emerald-400" />
                  <div>
                    <div className="text-sm font-bold">USB / Webcam</div>
                    <div className="text-[11px] text-gray-400">Direct Auto-Detect</div>
                  </div>
                </button>

                <button
                  type="button"
                  onClick={() => handleTypeSelect('phone')}
                  className={`p-4 rounded-2xl border text-left flex flex-col gap-2 transition-all ${
                    wizardType === 'phone'
                      ? 'border-blue-500 bg-blue-500/10 text-white'
                      : 'border-dark-700 bg-dark-900/50 text-gray-400 hover:text-white hover:border-dark-600'
                  }`}
                >
                  <Smartphone className="w-6 h-6 text-blue-400" />
                  <div>
                    <div className="text-sm font-bold">Phone Camera</div>
                    <div className="text-[11px] text-gray-400">Same Wi-Fi Stream</div>
                  </div>
                </button>

                <button
                  type="button"
                  onClick={() => handleTypeSelect('rtsp')}
                  className={`p-4 rounded-2xl border text-left flex flex-col gap-2 transition-all ${
                    wizardType === 'rtsp'
                      ? 'border-purple-500 bg-purple-500/10 text-white'
                      : 'border-dark-700 bg-dark-900/50 text-gray-400 hover:text-white hover:border-dark-600'
                  }`}
                >
                  <Video className="w-6 h-6 text-purple-400" />
                  <div>
                    <div className="text-sm font-bold">OBS / RTSP</div>
                    <div className="text-[11px] text-gray-400">CCTV &amp; Virtual</div>
                  </div>
                </button>
              </div>

              {/* USB TAB: DIRECT AUTO-DETECTION CARDS */}
              {wizardType === 'usb' && (
                <div className="space-y-3 bg-dark-900/60 border border-dark-700 p-4 rounded-2xl">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-white flex items-center gap-1.5">
                      <Cpu className="w-4 h-4 text-emerald-400" />
                      <span>Detected Physical Video Devices</span>
                    </span>
                    <button
                      type="button"
                      onClick={scanUsbCameras}
                      className="text-xs text-blue-400 hover:text-blue-300 flex items-center gap-1"
                    >
                      <RefreshCw className={`w-3.5 h-3.5 ${detectingUsb ? 'animate-spin' : ''}`} />
                      <span>Re-scan USB</span>
                    </button>
                  </div>

                  {detectingUsb ? (
                    <div className="p-4 text-center text-xs text-gray-400">Scanning USB buses...</div>
                  ) : detectedUsbCameras.length === 0 ? (
                    <div className="p-4 text-center text-xs text-gray-400">
                      No external USB cameras detected. Using primary built-in device (Index 0).
                    </div>
                  ) : (
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                      {detectedUsbCameras.map((dev) => {
                        const isSelected = sourceUrl === String(dev.index);
                        return (
                          <button
                            key={dev.index}
                            type="button"
                            onClick={() => selectUsbCamera(dev.index, dev.name)}
                            className={`p-3 rounded-xl border text-left flex items-center justify-between transition-all ${
                              isSelected
                                ? 'bg-emerald-500/15 border-emerald-500 text-white'
                                : 'bg-dark-800 border-dark-700 text-gray-300 hover:border-dark-600'
                            }`}
                          >
                            <div>
                              <div className="text-xs font-bold">{dev.name}</div>
                              <div className="text-[11px] font-mono text-gray-400">
                                Index {dev.index} &bull; {dev.resolution}
                              </div>
                            </div>
                            {isSelected && <CheckCircle2 className="w-4 h-4 text-emerald-400" />}
                          </button>
                        );
                      })}
                    </div>
                  )}
                </div>
              )}

              {/* PHONE TAB: SAME WI-FI STREAMING OPTIONS */}
              {wizardType === 'phone' && (
                <div className="space-y-4 bg-dark-900/60 border border-dark-700 p-4 rounded-2xl">
                  {/* Wi-Fi Status Bar */}
                  <div className="flex items-center justify-between bg-blue-500/10 border border-blue-500/20 px-3.5 py-2 rounded-xl text-xs">
                    <span className="text-blue-400 flex items-center gap-1.5 font-semibold">
                      <Wifi className="w-4 h-4" />
                      <span>Host Wi-Fi IP: <strong>{networkInfo.local_ip}</strong></span>
                    </span>
                    <span className="text-gray-400 font-mono text-[11px]">Subnet: {networkInfo.subnet}</span>
                  </div>

                  {/* Wi-Fi Scanner and Instructions */}
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-white flex items-center gap-1.5">
                        <Wifi className="w-4 h-4 text-blue-400" />
                        <span>Same Wi-Fi Phone Camera Detection</span>
                      </span>
                      <button
                        type="button"
                        onClick={scanWifiPhones}
                        disabled={scanningPhones}
                        className="text-xs font-bold px-3 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-white flex items-center gap-1.5 transition-colors disabled:opacity-50"
                      >
                        <RefreshCw className={`w-3.5 h-3.5 ${scanningPhones ? 'animate-spin' : ''}`} />
                        <span>{scanningPhones ? 'Scanning Wi-Fi...' : 'Auto-Detect Phone on Wi-Fi'}</span>
                      </button>
                    </div>

                    {/* Discovered Phone Cameras on Wi-Fi */}
                    {detectedPhones.length > 0 && (
                      <div className="space-y-2 bg-emerald-500/10 border border-emerald-500/30 p-3 rounded-xl">
                        <div className="text-xs font-bold text-emerald-400 flex items-center gap-1.5">
                          <CheckCircle2 className="w-4 h-4" />
                          <span>Discovered Phone Streams on Your Wi-Fi:</span>
                        </div>
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                          {detectedPhones.map((p, idx) => (
                            <button
                              key={idx}
                              type="button"
                              onClick={() => {
                                setSourceUrl(p.stream_url);
                                setCamName(p.suggested_name);
                                handleTestSource();
                              }}
                              className="p-2.5 rounded-lg bg-dark-800 border border-dark-700 hover:border-emerald-500 text-left flex items-center justify-between"
                            >
                              <div>
                                <div className="text-xs font-bold text-white">{p.type}</div>
                                <div className="text-[11px] font-mono text-emerald-400">{p.ip}:{p.port}</div>
                              </div>
                              <span className="text-[11px] text-blue-400 font-semibold">Select</span>
                            </button>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* 3-Step Setup Instructions */}
                    <div className="bg-dark-950/80 border border-dark-700/80 p-3.5 rounded-xl space-y-2 text-xs text-gray-300">
                      <div className="font-bold text-white flex items-center gap-2">
                        <span>How to stream phone camera on Wi-Fi:</span>
                      </div>
                      <ol className="list-decimal list-inside space-y-1 text-gray-300 text-[11.5px] leading-relaxed">
                        <li>Connect your phone to the <strong>same Wi-Fi network</strong> as your laptop.</li>
                        <li>Open free app <strong>IP Webcam</strong> (Android) or <strong>Live-Reporter / DroidCam</strong> (iOS) &amp; tap <em>"Start Server"</em>.</li>
                        <li>Click <strong>"Auto-Detect Phone on Wi-Fi"</strong> above (or enter the URL displayed on your phone below).</li>
                      </ol>
                    </div>

                    {/* Web Broadcaster Alternative Link */}
                    <div className="flex items-center justify-between p-2.5 rounded-xl bg-dark-950 border border-dark-700/50 text-[11px]">
                      <span className="text-gray-400 truncate">
                        Browser transmitter: <span className="text-blue-400 font-mono">{phoneBroadcastUrl}</span>
                      </span>
                      <button
                        type="button"
                        onClick={copyPhoneUrl}
                        className="px-2 py-1 bg-dark-800 hover:bg-dark-700 text-gray-200 rounded font-semibold shrink-0 ml-2"
                      >
                        {copiedLink ? 'Copied!' : 'Copy Link'}
                      </button>
                    </div>
                  </div>
                </div>
              )}

              {/* Form Fields */}
              <form onSubmit={handleSaveCamera} className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-semibold text-gray-400 mb-1">Camera ID</label>
                    <input
                      type="text"
                      required
                      value={camId}
                      onChange={(e) => setCamId(e.target.value)}
                      className="w-full bg-dark-900 border border-dark-700 rounded-xl px-3.5 py-2.5 text-sm text-white font-mono uppercase"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-gray-400 mb-1">Camera Name</label>
                    <input
                      type="text"
                      required
                      value={camName}
                      onChange={(e) => setCamName(e.target.value)}
                      className="w-full bg-dark-900 border border-dark-700 rounded-xl px-3.5 py-2.5 text-sm text-white"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-semibold text-gray-400 mb-1">Location Label</label>
                    <input
                      type="text"
                      value={camLocation}
                      onChange={(e) => setCamLocation(e.target.value)}
                      placeholder="e.g. Front Door, Lobby"
                      className="w-full bg-dark-900 border border-dark-700 rounded-xl px-3.5 py-2.5 text-sm text-white"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-gray-400 mb-1">Security Zone</label>
                    <select
                      value={camZone}
                      onChange={(e) => setCamZone(e.target.value)}
                      className="w-full bg-dark-900 border border-dark-700 rounded-xl px-3.5 py-2.5 text-sm text-white"
                    >
                      {zones.length > 0 ? (
                        zones.map((z) => (
                          <option key={z.zone_id} value={z.name}>
                            {z.name}
                          </option>
                        ))
                      ) : (
                        <>
                          <option value="Entry Zone A">Entry Zone A</option>
                          <option value="Lobby Zone B">Lobby Zone B</option>
                          <option value="Server Room">Server Room</option>
                        </>
                      )}
                    </select>
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-gray-400 mb-1">
                    Camera Device / Stream Source
                  </label>
                  <div className="flex gap-2">
                    <input
                      type="text"
                      required
                      value={sourceUrl}
                      onChange={(e) => setSourceUrl(e.target.value)}
                      className="flex-1 bg-dark-900 border border-dark-700 rounded-xl px-3.5 py-2.5 text-sm text-white font-mono"
                    />
                    <button
                      type="button"
                      onClick={handleTestSource}
                      disabled={testing || !sourceUrl}
                      className="px-4 py-2.5 bg-dark-700 hover:bg-dark-600 text-gray-200 text-xs font-bold rounded-xl flex items-center gap-1.5 transition-colors disabled:opacity-50 shrink-0"
                    >
                      {testing ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Play className="w-3.5 h-3.5 text-emerald-400" />}
                      <span>Test &amp; Preview</span>
                    </button>
                  </div>
                </div>

                {/* Live Test Preview Box */}
                {testResult && (
                  <div
                    className={`p-4 rounded-xl border flex items-start gap-3 ${
                      testResult.success ? 'bg-emerald-500/10 border-emerald-500/30' : 'bg-red-500/10 border-red-500/30'
                    }`}
                  >
                    {testResult.success ? (
                      <CheckCircle2 className="w-5 h-5 text-emerald-400 shrink-0 mt-0.5" />
                    ) : (
                      <AlertCircle className="w-5 h-5 text-red-400 shrink-0 mt-0.5" />
                    )}

                    <div className="flex-1 min-w-0">
                      <div className="text-xs font-bold text-white">
                        {testResult.success ? 'Camera Verified & Ready' : 'Connection Check'}
                      </div>
                      <div className="text-xs text-gray-300 mt-0.5">{testResult.message}</div>
                      {testResult.resolution && (
                        <div className="text-[11px] font-mono text-emerald-400 mt-1">
                          Detected Resolution: {testResult.resolution}
                        </div>
                      )}

                      {testResult.preview_base64 && (
                        <div className="mt-3 aspect-video w-48 rounded-lg overflow-hidden border border-emerald-500/40">
                          <img src={testResult.preview_base64} alt="Camera Preview" className="w-full h-full object-cover" />
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {/* Submit Buttons */}
                <div className="flex items-center justify-end gap-3 pt-2">
                  <button
                    type="button"
                    onClick={() => setShowWizard(false)}
                    className="px-4 py-2.5 rounded-xl bg-dark-700 hover:bg-dark-600 text-gray-300 text-xs font-semibold"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={saving}
                    className="px-6 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white text-xs font-bold transition-colors disabled:opacity-50"
                  >
                    {saving ? 'Linking...' : 'Connect Camera to Perimeter'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
