import React, { useState, useRef, useEffect } from 'react';
import { api } from '../api';
import { Camera, CheckCircle2, AlertCircle, Upload, RefreshCw } from 'lucide-react';

export default function AddEmployee({ onEmployeeAdded }) {
  const [empId, setEmpId] = useState('');
  const [name, setName] = useState('');
  const [department, setDepartment] = useState('Engineering');
  const [accessLevel, setAccessLevel] = useState(1);
  const [faceImageBase64, setFaceImageBase64] = useState('');
  const [isCameraActive, setIsCameraActive] = useState(false);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState(null);

  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const streamRef = useRef(null);

  useEffect(() => {
    if (isCameraActive && videoRef.current && streamRef.current) {
      videoRef.current.srcObject = streamRef.current;
      videoRef.current.play().catch((err) => console.log('Video play catch:', err));
    }
  }, [isCameraActive]);

  useEffect(() => {
    return () => {
      stopCamera();
    };
  }, []);

  const startCamera = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'user', width: { ideal: 640 }, height: { ideal: 480 } },
        audio: false
      });
      streamRef.current = stream;
      setIsCameraActive(true);
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        videoRef.current.play().catch(() => {});
      }
    } catch (err) {
      console.error('Camera access error:', err);
      setMessage({ type: 'error', text: 'Webcam access denied or in use by another tab/app. You can upload a photo instead.' });
    }
  };

  const stopCamera = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((t) => t.stop());
      streamRef.current = null;
    }
    setIsCameraActive(false);
  };

  const capturePhoto = () => {
    if (!videoRef.current || !canvasRef.current) return;
    const video = videoRef.current;
    const canvas = canvasRef.current;
    canvas.width = video.videoWidth || 640;
    canvas.height = video.videoHeight || 480;
    const ctx = canvas.getContext('2d');
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    const dataUrl = canvas.toDataURL('image/jpeg', 0.85);
    setFaceImageBase64(dataUrl);
    stopCamera();
  };

  const handleFileUpload = (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = () => {
      setFaceImageBase64(reader.result);
    };
    reader.readAsDataURL(file);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!faceImageBase64) {
      setMessage({ type: 'error', text: 'Please capture or upload an employee photo for biometric registration.' });
      return;
    }

    setLoading(true);
    setMessage(null);

    try {
      const payload = {
        employee_id: empId.trim().toUpperCase(),
        name: name.trim(),
        department,
        access_level: parseInt(accessLevel, 10),
        face_image_base64: faceImageBase64
      };

      await api.registerEmployee(payload);
      setMessage({
        type: 'success',
        text: `Successfully enrolled ${name} (${empId})! 512-dim face & body vectors encrypted with AES-256 and stored in Redis.`
      });

      // Reset form
      setEmpId('');
      setName('');
      setFaceImageBase64('');
      if (onEmployeeAdded) onEmployeeAdded();
    } catch (err) {
      setMessage({ type: 'error', text: err.message || 'Failed to register employee.' });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      <div>
        <h2 className="text-2xl font-bold text-white tracking-tight">Enroll New Employee</h2>
        <p className="text-sm text-gray-400 mt-1">
          Capture employee facial and body biometrics. Embeddings will be automatically generated and encrypted at rest with AES-256.
        </p>
      </div>

      {message && (
        <div
          className={`p-4 rounded-xl flex items-center gap-3 text-sm ${
            message.type === 'success'
              ? 'bg-emerald-500/10 border border-emerald-500/20 text-emerald-400'
              : 'bg-red-500/10 border border-red-500/20 text-red-400'
          }`}
        >
          {message.type === 'success' ? <CheckCircle2 className="w-5 h-5 shrink-0" /> : <AlertCircle className="w-5 h-5 shrink-0" />}
          <span>{message.text}</span>
        </div>
      )}

      <form onSubmit={handleSubmit} className="grid grid-cols-1 md:grid-cols-2 gap-8">
        {/* Left: Metadata Inputs */}
        <div className="bg-dark-800 border border-dark-700 p-6 rounded-2xl space-y-5">
          <h3 className="text-base font-semibold text-white">Employee Profile</h3>

          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-gray-400 mb-2">Badge / Card ID</label>
            <input
              type="text"
              required
              placeholder="e.g. EMP002"
              value={empId}
              onChange={(e) => setEmpId(e.target.value)}
              className="w-full bg-dark-900 border border-dark-700 rounded-xl px-4 py-3 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-blue-500 uppercase"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-gray-400 mb-2">Full Name</label>
            <input
              type="text"
              required
              placeholder="e.g. Sarah Connor"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full bg-dark-900 border border-dark-700 rounded-xl px-4 py-3 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-blue-500"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-gray-400 mb-2">Department</label>
              <select
                value={department}
                onChange={(e) => setDepartment(e.target.value)}
                className="w-full bg-dark-900 border border-dark-700 rounded-xl px-4 py-3 text-sm text-white focus:outline-none focus:border-blue-500"
              >
                <option value="Engineering">Engineering</option>
                <option value="Marketing">Marketing</option>
                <option value="Security">Security</option>
                <option value="Operations">Operations</option>
                <option value="HR">HR</option>
                <option value="Finance">Finance</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-gray-400 mb-2">Clearance Level</label>
              <select
                value={accessLevel}
                onChange={(e) => setAccessLevel(Number(e.target.value))}
                className="w-full bg-dark-900 border border-dark-700 rounded-xl px-4 py-3 text-sm text-white focus:outline-none focus:border-blue-500"
              >
                <option value={1}>Level 1 (General)</option>
                <option value={2}>Level 2 (Standard)</option>
                <option value={3}>Level 3 (Elevated)</option>
                <option value={4}>Level 4 (Secure)</option>
                <option value={5}>Level 5 (Top Secret)</option>
              </select>
            </div>
          </div>
        </div>

        {/* Right: Biometric Capture */}
        <div className="bg-dark-800 border border-dark-700 p-6 rounded-2xl space-y-5 flex flex-col">
          <h3 className="text-base font-semibold text-white">Biometric Capture (Face &amp; Body)</h3>

          <div className="flex-1 min-h-[260px] bg-dark-900 border border-dark-700 rounded-xl overflow-hidden relative flex items-center justify-center">
            {isCameraActive ? (
              <div className="relative w-full h-full flex items-center justify-center">
                <video ref={videoRef} autoPlay playsInline muted className="w-full h-full object-cover scale-x-[-1]" />
                <div className="absolute inset-0 border-2 border-blue-500/40 rounded-xl pointer-events-none" />
              </div>
            ) : faceImageBase64 ? (
              <div className="relative w-full h-full">
                <img src={faceImageBase64} alt="Captured Profile" className="w-full h-full object-cover" />
                <div className="absolute bottom-3 right-3 px-2 py-1 rounded bg-emerald-500/90 text-white text-xs font-bold">
                  Ready for AI Analysis
                </div>
              </div>
            ) : (
              <div className="text-center p-6 text-gray-500">
                <Camera className="w-12 h-12 mx-auto mb-2 opacity-50" />
                <p className="text-sm">No photo captured yet.</p>
                <p className="text-xs text-gray-600 mt-1">Use your camera or upload an employee photo.</p>
              </div>
            )}
            <canvas ref={canvasRef} className="hidden" />
          </div>

          <div className="flex gap-3">
            {isCameraActive ? (
              <button
                type="button"
                onClick={capturePhoto}
                className="flex-1 py-2.5 px-4 bg-emerald-600 hover:bg-emerald-500 text-white text-sm font-semibold rounded-xl transition-colors flex items-center justify-center gap-2"
              >
                <Camera className="w-4 h-4" />
                <span>Snap Photo</span>
              </button>
            ) : (
              <button
                type="button"
                onClick={startCamera}
                className="flex-1 py-2.5 px-4 bg-dark-700 hover:bg-dark-600 text-white text-sm font-semibold rounded-xl transition-colors flex items-center justify-center gap-2"
              >
                <Camera className="w-4 h-4" />
                <span>Use Webcam</span>
              </button>
            )}

            <label className="flex-1 py-2.5 px-4 bg-dark-700 hover:bg-dark-600 text-gray-300 text-sm font-semibold rounded-xl transition-colors flex items-center justify-center gap-2 cursor-pointer">
              <Upload className="w-4 h-4" />
              <span>Upload File</span>
              <input type="file" accept="image/*" onChange={handleFileUpload} className="hidden" />
            </label>
          </div>
        </div>

        {/* Submit */}
        <div className="md:col-span-2">
          <button
            type="submit"
            disabled={loading}
            className="w-full py-3.5 px-6 bg-blue-600 hover:bg-blue-500 text-white font-semibold rounded-xl shadow-lg shadow-blue-600/20 transition-all disabled:opacity-50 flex items-center justify-center gap-2"
          >
            {loading ? (
              <>
                <RefreshCw className="w-5 h-5 animate-spin" />
                <span>Extracting Biometric Embeddings &amp; Encrypting...</span>
              </>
            ) : (
              <span>Complete Biometric Enrollment &rarr;</span>
            )}
          </button>
        </div>
      </form>
    </div>
  );
}
