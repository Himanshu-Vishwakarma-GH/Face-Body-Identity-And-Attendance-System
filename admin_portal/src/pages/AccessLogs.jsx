import React, { useState, useEffect } from 'react';
import { api } from '../api';
import { Filter, RefreshCw } from 'lucide-react';

export default function AccessLogs() {
  const [logs, setLogs] = useState([]);
  const [decision, setDecision] = useState('');
  const [loading, setLoading] = useState(true);

  const fetchLogs = async () => {
    setLoading(true);
    try {
      const data = await api.getAccessLogs(100, decision);
      setLogs(data);
    } catch (err) {
      console.error('Failed to load logs:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs();
  }, [decision]);

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-white tracking-tight">Security Access Logs</h2>
          <p className="text-sm text-gray-400 mt-1">Audit trail of all entry verifications, denials, and security alerts.</p>
        </div>

        <button
          onClick={fetchLogs}
          className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-dark-800 border border-dark-700 hover:bg-dark-700 text-sm font-medium text-gray-200 transition-colors"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          <span>Refresh</span>
        </button>
      </div>

      {/* Filter */}
      <div className="flex items-center gap-3 bg-dark-800 border border-dark-700 p-4 rounded-2xl">
        <Filter className="w-5 h-5 text-gray-500" />
        <span className="text-xs font-semibold uppercase tracking-wider text-gray-400">Filter Decision:</span>
        <select
          value={decision}
          onChange={(e) => setDecision(e.target.value)}
          className="bg-dark-900 border border-dark-700 rounded-xl px-4 py-2 text-sm text-white focus:outline-none focus:border-blue-500"
        >
          <option value="">All Decisions</option>
          <option value="GRANTED">GRANTED Only</option>
          <option value="DENIED">DENIED Only</option>
          <option value="WARNING">WARNING Only</option>
        </select>
      </div>

      {/* Logs Table */}
      <div className="bg-dark-800 border border-dark-700 rounded-2xl overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="text-xs uppercase tracking-wider text-gray-400 bg-dark-900/50 border-b border-dark-700">
              <tr>
                <th className="px-6 py-4 font-semibold">Timestamp</th>
                <th className="px-6 py-4 font-semibold">Employee</th>
                <th className="px-6 py-4 font-semibold">Camera &amp; Zone</th>
                <th className="px-6 py-4 font-semibold">Decision</th>
                <th className="px-6 py-4 font-semibold">Face Match</th>
                <th className="px-6 py-4 font-semibold">Body Match</th>
                <th className="px-6 py-4 font-semibold">Tailgating</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-dark-700/50">
              {logs.length === 0 ? (
                <tr>
                  <td colSpan="7" className="px-6 py-10 text-center text-gray-500">
                    No access log entries found.
                  </td>
                </tr>
              ) : (
                logs.map((log) => {
                  const isGranted = log.decision === 'GRANTED';
                  const isWarning = log.decision === 'WARNING';
                  const dateStr = new Date(log.timestamp * 1000).toLocaleString();

                  return (
                    <tr key={log.log_id} className="hover:bg-dark-700/20 transition-colors">
                      <td className="px-6 py-4 text-xs font-mono text-gray-400">
                        {dateStr}
                      </td>
                      <td className="px-6 py-4">
                        <div className="font-semibold text-white">{log.employee_name || 'Unidentified'}</div>
                        <div className="text-xs text-gray-400">{log.employee_id || 'No ID'}</div>
                      </td>
                      <td className="px-6 py-4">
                        <div className="text-white font-medium">{log.camera_id}</div>
                        <div className="text-xs text-gray-500">{log.zone}</div>
                      </td>
                      <td className="px-6 py-4">
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
                      <td className="px-6 py-4 font-mono text-xs text-gray-300">
                        {Math.round(log.face_confidence * 100)}%
                      </td>
                      <td className="px-6 py-4 font-mono text-xs text-gray-300">
                        {Math.round(log.body_confidence * 100)}%
                      </td>
                      <td className="px-6 py-4">
                        {log.tailgate_detected ? (
                          <span className="bg-red-500/10 text-red-400 px-2 py-0.5 rounded text-xs font-bold">
                            ALERT
                          </span>
                        ) : (
                          <span className="text-gray-500 text-xs">No</span>
                        )}
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
  );
}
