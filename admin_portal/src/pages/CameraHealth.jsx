import React, { useState, useEffect } from 'react';
import { api } from '../api';
import { Activity, AlertTriangle, CheckCircle, RefreshCw, Wrench } from 'lucide-react';

export default function CameraHealth() {
  const [healthData, setHealthData] = useState(null);
  const [tickets, setTickets] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchHealth = async () => {
    setLoading(true);
    try {
      const [h, t] = await Promise.all([
        api.getCameraHealth(),
        api.getTickets()
      ]);
      setHealthData(h);
      setTickets(t);
    } catch (err) {
      console.error('Failed to load health reports:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHealth();
  }, []);

  const handleResolve = async (ticketId) => {
    try {
      await api.resolveTicket(ticketId);
      fetchHealth();
    } catch (err) {
      alert('Failed to resolve ticket: ' + err.message);
    }
  };

  return (
    <div className="space-y-8">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-white tracking-tight">Camera Health Monitoring</h2>
          <p className="text-sm text-gray-400 mt-1">
            Autonomous heartbeat monitoring. Unresponsive devices are automatically flagged and queued for maintenance.
          </p>
        </div>

        <button
          onClick={fetchHealth}
          className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-sm font-semibold text-white shadow-lg shadow-blue-600/20 transition-all"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          <span>Run Diagnostic Ping</span>
        </button>
      </div>

      {/* Diagnostics Summary */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-5">
        <div className="bg-dark-800 border border-dark-700 p-6 rounded-2xl">
          <div className="text-xs font-semibold uppercase tracking-wider text-gray-400">Total Monitored</div>
          <div className="text-3xl font-extrabold text-white mt-2">{healthData?.cameras_checked || 0}</div>
        </div>

        <div className="bg-dark-800 border border-dark-700 p-6 rounded-2xl">
          <div className="text-xs font-semibold uppercase tracking-wider text-gray-400">Issues Flagged</div>
          <div className="text-3xl font-extrabold text-red-400 mt-2">{healthData?.issues_flagged || 0}</div>
        </div>

        <div className="bg-dark-800 border border-dark-700 p-6 rounded-2xl">
          <div className="text-xs font-semibold uppercase tracking-wider text-gray-400">Open Tickets</div>
          <div className="text-3xl font-extrabold text-amber-400 mt-2">
            {tickets.filter((t) => t.status === 'OPEN').length}
          </div>
        </div>
      </div>

      {/* Auto-Reported Tickets Section */}
      <div className="space-y-4">
        <h3 className="text-lg font-bold text-white flex items-center gap-2">
          <Wrench className="w-5 h-5 text-amber-400" />
          <span>Automated Maintenance Tickets ({tickets.length})</span>
        </h3>

        <div className="bg-dark-800 border border-dark-700 rounded-2xl overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="text-xs uppercase tracking-wider text-gray-400 bg-dark-900/50 border-b border-dark-700">
                <tr>
                  <th className="px-6 py-4 font-semibold">Ticket ID</th>
                  <th className="px-6 py-4 font-semibold">Camera</th>
                  <th className="px-6 py-4 font-semibold">Severity</th>
                  <th className="px-6 py-4 font-semibold">Diagnosis Issue</th>
                  <th className="px-6 py-4 font-semibold">Status</th>
                  <th className="px-6 py-4 font-semibold text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-dark-700/50">
                {tickets.length === 0 ? (
                  <tr>
                    <td colSpan="6" className="px-6 py-10 text-center text-emerald-400">
                      <div className="flex items-center justify-center gap-2">
                        <CheckCircle className="w-5 h-5" />
                        <span>All cameras operating normally! Zero open maintenance tickets.</span>
                      </div>
                    </td>
                  </tr>
                ) : (
                  tickets.map((ticket) => {
                    const isOpen = ticket.status === 'OPEN';
                    return (
                      <tr key={ticket.ticket_id} className="hover:bg-dark-700/20 transition-colors">
                        <td className="px-6 py-4 font-mono text-xs font-semibold text-blue-400">
                          {ticket.ticket_id}
                        </td>
                        <td className="px-6 py-4 font-bold text-white">
                          {ticket.camera_id}
                        </td>
                        <td className="px-6 py-4">
                          <span
                            className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-bold ${
                              ticket.severity === 'CRITICAL'
                                ? 'bg-red-500/10 text-red-400 border border-red-500/20'
                                : 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
                            }`}
                          >
                            {ticket.severity}
                          </span>
                        </td>
                        <td className="px-6 py-4 text-gray-300 text-xs font-medium">
                          {ticket.issue}
                        </td>
                        <td className="px-6 py-4">
                          <span
                            className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold ${
                              isOpen ? 'bg-amber-500/10 text-amber-400' : 'bg-emerald-500/10 text-emerald-400'
                            }`}
                          >
                            {ticket.status}
                          </span>
                        </td>
                        <td className="px-6 py-4 text-right">
                          {isOpen && (
                            <button
                              onClick={() => handleResolve(ticket.ticket_id)}
                              className="px-3 py-1 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold rounded-lg transition-colors"
                            >
                              Resolve
                            </button>
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
    </div>
  );
}
