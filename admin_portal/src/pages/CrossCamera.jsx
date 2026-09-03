import React, { useState, useEffect } from 'react';
import { api } from '../api';
import { MapPin, Search, ArrowRight, Clock, ShieldCheck, RefreshCw } from 'lucide-react';

export default function CrossCamera() {
  const [employeeId, setEmployeeId] = useState('');
  const [timeline, setTimeline] = useState([]);
  const [movementPath, setMovementPath] = useState(null);
  const [loading, setLoading] = useState(false);

  const fetchTimeline = async (empId = '') => {
    setLoading(true);
    try {
      const data = await api.getTimeline(empId);
      setTimeline(data);

      if (empId) {
        const pathData = await api.getEmployeeMovementPath(empId);
        setMovementPath(pathData);
      } else {
        setMovementPath(null);
      }
    } catch (err) {
      console.error('Failed to load cross-camera timeline:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTimeline();
  }, []);

  const handleSearch = (e) => {
    e.preventDefault();
    fetchTimeline(employeeId.trim().toUpperCase());
  };

  return (
    <div className="space-y-8">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-white tracking-tight">Cross-Camera Movement Tracking</h2>
          <p className="text-sm text-gray-400 mt-1">
            Interlinks surveillance data across camera zones to reconstruct employee motion journeys.
          </p>
        </div>

        <button
          onClick={() => fetchTimeline(employeeId)}
          className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-dark-800 border border-dark-700 hover:bg-dark-700 text-sm font-medium text-gray-200 transition-colors"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          <span>Refresh</span>
        </button>
      </div>

      {/* Employee Search Form */}
      <form onSubmit={handleSearch} className="flex gap-4 bg-dark-800 border border-dark-700 p-4 rounded-2xl">
        <div className="flex-1 relative">
          <Search className="w-5 h-5 absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-500" />
          <input
            type="text"
            placeholder="Filter journey by Employee ID (e.g. EMP001)..."
            value={employeeId}
            onChange={(e) => setEmployeeId(e.target.value)}
            className="w-full bg-dark-900 border border-dark-700 rounded-xl pl-11 pr-4 py-2.5 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-blue-500 uppercase"
          />
        </div>
        <button
          type="submit"
          className="px-6 py-2.5 bg-blue-600 hover:bg-blue-500 text-white font-semibold text-sm rounded-xl transition-colors"
        >
          Trace Path
        </button>
        {employeeId && (
          <button
            type="button"
            onClick={() => { setEmployeeId(''); fetchTimeline(''); }}
            className="px-4 py-2.5 bg-dark-700 hover:bg-dark-600 text-gray-300 font-semibold text-sm rounded-xl transition-colors"
          >
            Clear
          </button>
        )}
      </form>

      {/* Spatial Path Card if employee selected */}
      {movementPath && movementPath.path?.length > 0 && (
        <div className="bg-dark-800 border border-blue-500/30 p-6 rounded-2xl space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-base font-bold text-white flex items-center gap-2">
              <MapPin className="w-5 h-5 text-blue-400" />
              <span>Spatial Journey for {movementPath.employee_id}</span>
            </h3>
            <span className="text-xs font-semibold text-blue-400 bg-blue-500/10 px-2.5 py-1 rounded-md">
              {movementPath.total_checkpoints_today} Checkpoints Visited
            </span>
          </div>

          <div className="flex flex-wrap items-center gap-3 pt-2">
            {movementPath.path.map((pt, idx) => (
              <React.Fragment key={idx}>
                <div className="bg-dark-900 border border-dark-700 p-3.5 rounded-xl">
                  <div className="text-xs font-bold text-blue-400">Step {pt.step} &bull; {pt.time}</div>
                  <div className="font-semibold text-white mt-1 text-sm">{pt.camera_name}</div>
                  <div className="text-xs text-gray-400 mt-0.5">{pt.zone}</div>
                </div>
                {idx < movementPath.path.length - 1 && (
                  <ArrowRight className="w-5 h-5 text-gray-500 shrink-0" />
                )}
              </React.Fragment>
            ))}
          </div>
        </div>
      )}

      {/* Unified Timeline List */}
      <div className="bg-dark-800 border border-dark-700 rounded-2xl p-6 space-y-6">
        <h3 className="text-lg font-bold text-white">Unified Security Timeline</h3>

        <div className="space-y-4">
          {timeline.length === 0 ? (
            <div className="text-center py-10 text-gray-500">
              No cross-camera movements recorded yet.
            </div>
          ) : (
            timeline.map((item) => {
              const isGranted = item.decision === 'GRANTED';
              return (
                <div
                  key={item.log_id}
                  className="flex items-start gap-4 p-4 rounded-xl bg-dark-900/60 border border-dark-700/50 hover:border-dark-600 transition-colors"
                >
                  <div className="p-2.5 rounded-xl bg-blue-500/10 text-blue-400 mt-0.5">
                    <Clock className="w-5 h-5" />
                  </div>

                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between">
                      <div className="font-semibold text-white text-base">
                        {item.employee_name} <span className="text-xs font-normal text-gray-400">({item.employee_id})</span>
                      </div>
                      <span className="text-xs font-mono text-gray-400">{item.formatted_time} &bull; {item.date}</span>
                    </div>

                    <div className="text-sm text-gray-300 mt-1">
                      Detected at <strong className="text-white">{item.camera_name} ({item.camera_id})</strong> in <span className="text-blue-400">{item.zone}</span>
                    </div>

                    <div className="flex items-center gap-3 mt-3 text-xs">
                      <span className={`px-2 py-0.5 rounded-full font-semibold ${isGranted ? 'bg-emerald-500/10 text-emerald-400' : 'bg-red-500/10 text-red-400'}`}>
                        {item.decision}
                      </span>
                      <span className="text-gray-400 font-mono">
                        Face: {Math.round(item.face_confidence * 100)}% &bull; Body: {Math.round(item.body_confidence * 100)}%
                      </span>
                      {item.tailgate_detected && (
                        <span className="bg-red-500/10 text-red-400 px-2 py-0.5 rounded font-bold">
                          TAILGATE ALERT
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              );
            })
          )}
        </div>
      </div>
    </div>
  );
}
