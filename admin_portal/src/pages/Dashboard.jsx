import React, { useState, useEffect } from 'react';
import { api } from '../api';
import { Users, UserCheck, Camera, ShieldAlert, ExternalLink, RefreshCw } from 'lucide-react';

export default function Dashboard({ onNavigate }) {
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);

  const loadData = async () => {
    try {
      setLoading(true);
      const data = await api.getDashboard();
      setSummary(data);
    } catch (err) {
      console.error('Failed to load dashboard summary:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
    const timer = setInterval(loadData, 10000);
    return () => clearInterval(timer);
  }, []);

  if (loading && !summary) {
    return (
      <div className="flex items-center justify-center h-64 text-gray-400">
        <RefreshCw className="w-6 h-6 animate-spin mr-2" />
        <span>Loading attendance & security metrics...</span>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Top Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-dark-800 border border-dark-700 p-6 rounded-2xl">
        <div>
          <h2 className="text-2xl font-bold text-white tracking-tight">Security Overview</h2>
          <p className="text-sm text-gray-400 mt-1">Real-time attendance tracking and camera surveillance monitoring.</p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={loadData}
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-dark-700 hover:bg-dark-600 text-sm font-medium text-gray-200 transition-colors"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            <span>Refresh</span>
          </button>
          <a
            href="http://localhost:8000/camera"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-sm font-medium text-white shadow-lg shadow-blue-600/20 transition-all"
          >
            <ExternalLink className="w-4 h-4" />
            <span>Open Entry Kiosk</span>
          </a>
        </div>
      </div>

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        <div className="bg-dark-800 border border-dark-700 p-6 rounded-2xl">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-gray-400">Total Enrolled</span>
            <div className="p-2.5 rounded-xl bg-blue-500/10 text-blue-500"><Users className="w-5 h-5" /></div>
          </div>
          <div className="mt-4">
            <span className="text-3xl font-extrabold text-white">{summary?.total_employees || 0}</span>
            <span className="text-xs text-gray-400 ml-2">employees</span>
          </div>
        </div>

        <div className="bg-dark-800 border border-dark-700 p-6 rounded-2xl">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-gray-400">Present Today</span>
            <div className="p-2.5 rounded-xl bg-emerald-500/10 text-emerald-500"><UserCheck className="w-5 h-5" /></div>
          </div>
          <div className="mt-4 flex items-baseline gap-2">
            <span className="text-3xl font-extrabold text-white">{summary?.present_today || 0}</span>
            <span className="text-sm font-semibold text-emerald-400">({summary?.attendance_rate || 0}%)</span>
          </div>
        </div>

        <div className="bg-dark-800 border border-dark-700 p-6 rounded-2xl">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-gray-400">Active Cameras</span>
            <div className="p-2.5 rounded-xl bg-indigo-500/10 text-indigo-500"><Camera className="w-5 h-5" /></div>
          </div>
          <div className="mt-4">
            <span className="text-3xl font-extrabold text-white">{summary?.active_cameras || 0}</span>
            <span className="text-xs text-gray-400 ml-2">/ {summary?.total_cameras || 0} linked</span>
          </div>
        </div>

        <div className="bg-dark-800 border border-dark-700 p-6 rounded-2xl">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-gray-400">Tailgate Alerts</span>
            <div className="p-2.5 rounded-xl bg-red-500/10 text-red-500"><ShieldAlert className="w-5 h-5" /></div>
          </div>
          <div className="mt-4">
            <span className="text-3xl font-extrabold text-white">{summary?.tailgate_alerts_today || 0}</span>
            <span className="text-xs text-red-400 ml-2">alerts today</span>
          </div>
        </div>
      </div>

      {/* Two Column Layout: Department Attendance + Recent Logs */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left 1 Col: Department Breakdown */}
        <div className="bg-dark-800 border border-dark-700 p-6 rounded-2xl space-y-5">
          <h3 className="text-lg font-bold text-white">Department Attendance</h3>
          <div className="space-y-4">
            {summary?.department_stats?.length === 0 ? (
              <p className="text-sm text-gray-500">No department data recorded yet.</p>
            ) : (
              summary?.department_stats?.map((dept) => (
                <div key={dept.department} className="space-y-1.5">
                  <div className="flex justify-between text-sm">
                    <span className="font-medium text-gray-300">{dept.department}</span>
                    <span className="text-gray-400 font-mono text-xs">
                      {dept.present_count} / {dept.total_count} ({dept.percentage}%)
                    </span>
                  </div>
                  <div className="w-full h-2 rounded-full bg-dark-700 overflow-hidden">
                    <div
                      className="h-full rounded-full bg-blue-500 transition-all duration-500"
                      style={{ width: `${Math.min(100, dept.percentage)}%` }}
                    />
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Right 2 Cols: Recent Checkpoints */}
        <div className="lg:col-span-2 bg-dark-800 border border-dark-700 p-6 rounded-2xl space-y-5">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-bold text-white">Recent Entry Logs</h3>
            <button
              onClick={() => onNavigate('logs')}
              className="text-xs font-semibold text-blue-400 hover:text-blue-300 transition-colors"
            >
              View All Logs &rarr;
            </button>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="text-xs uppercase tracking-wider text-gray-400 border-b border-dark-700">
                <tr>
                  <th className="pb-3 font-semibold">Employee</th>
                  <th className="pb-3 font-semibold">Camera / Zone</th>
                  <th className="pb-3 font-semibold">Decision</th>
                  <th className="pb-3 font-semibold">Confidence</th>
                  <th className="pb-3 font-semibold">Time</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-dark-700/50">
                {summary?.recent_logs?.length === 0 ? (
                  <tr>
                    <td colSpan="5" className="py-6 text-center text-gray-500">No recent check-in attempts.</td>
                  </tr>
                ) : (
                  summary?.recent_logs?.map((log) => {
                    const isGranted = log.decision === 'GRANTED';
                    const isWarning = log.decision === 'WARNING';
                    const timeStr = new Date(log.timestamp * 1000).toLocaleTimeString();

                    return (
                      <tr key={log.log_id} className="hover:bg-dark-700/30 transition-colors">
                        <td className="py-3.5">
                          <div className="font-semibold text-white">{log.employee_name || 'Unidentified'}</div>
                          <div className="text-xs text-gray-400">{log.employee_id || 'No ID'} &bull; {log.department || 'N/A'}</div>
                        </td>
                        <td className="py-3.5">
                          <div className="text-gray-300 font-medium">{log.camera_id}</div>
                          <div className="text-xs text-gray-500">{log.zone}</div>
                        </td>
                        <td className="py-3.5">
                          <span
                            className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-bold ${
                              isGranted
                                ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                                : isWarning
                                ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
                                : 'bg-red-500/10 text-red-400 border border-red-500/20'
                            }`}
                          >
                            {log.decision}
                          </span>
                        </td>
                        <td className="py-3.5 text-xs font-mono text-gray-400">
                          Face: {Math.round(log.face_confidence * 100)}% &bull; Body: {Math.round(log.body_confidence * 100)}%
                        </td>
                        <td className="py-3.5 text-xs text-gray-500 font-mono">
                          {timeStr}
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
