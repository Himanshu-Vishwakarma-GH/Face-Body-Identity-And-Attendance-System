import React, { useState, useEffect } from 'react';
import { api } from '../api';
import { Search, UserX, Shield, Check, RefreshCw } from 'lucide-react';

export default function EmployeeList() {
  const [employees, setEmployees] = useState([]);
  const [search, setSearch] = useState('');
  const [department, setDepartment] = useState('');
  const [loading, setLoading] = useState(true);

  const fetchEmployees = async () => {
    setLoading(true);
    try {
      const data = await api.getEmployees(department);
      setEmployees(data);
    } catch (err) {
      console.error('Failed to load employees:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchEmployees();
  }, [department]);

  const handleDeactivate = async (empId) => {
    if (!confirm(`Are you sure you want to deactivate ${empId}?`)) return;
    try {
      await api.deactivateEmployee(empId);
      fetchEmployees();
    } catch (err) {
      alert('Failed to deactivate employee: ' + err.message);
    }
  };

  const filtered = employees.filter((e) => {
    const q = search.toLowerCase();
    return e.name.toLowerCase().includes(q) || e.employee_id.toLowerCase().includes(q);
  });

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-white tracking-tight">Employee Directory</h2>
          <p className="text-sm text-gray-400 mt-1">Manage enrolled employees and security clearance levels.</p>
        </div>

        <button
          onClick={fetchEmployees}
          className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-dark-800 border border-dark-700 hover:bg-dark-700 text-sm font-medium text-gray-200 transition-colors"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          <span>Refresh</span>
        </button>
      </div>

      {/* Filter & Search Bar */}
      <div className="flex flex-col sm:flex-row gap-4 bg-dark-800 border border-dark-700 p-4 rounded-2xl">
        <div className="flex-1 relative">
          <Search className="w-5 h-5 absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-500" />
          <input
            type="text"
            placeholder="Search by name or badge ID..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full bg-dark-900 border border-dark-700 rounded-xl pl-11 pr-4 py-2.5 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-blue-500"
          />
        </div>

        <select
          value={department}
          onChange={(e) => setDepartment(e.target.value)}
          className="bg-dark-900 border border-dark-700 rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:border-blue-500"
        >
          <option value="">All Departments</option>
          <option value="Engineering">Engineering</option>
          <option value="Marketing">Marketing</option>
          <option value="Security">Security</option>
          <option value="Operations">Operations</option>
          <option value="HR">HR</option>
          <option value="Finance">Finance</option>
        </select>
      </div>

      {/* Employees Table */}
      <div className="bg-dark-800 border border-dark-700 rounded-2xl overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="text-xs uppercase tracking-wider text-gray-400 bg-dark-900/50 border-b border-dark-700">
              <tr>
                <th className="px-6 py-4 font-semibold">Employee</th>
                <th className="px-6 py-4 font-semibold">Department</th>
                <th className="px-6 py-4 font-semibold">Clearance</th>
                <th className="px-6 py-4 font-semibold">Biometrics Enrolled</th>
                <th className="px-6 py-4 font-semibold">Status</th>
                <th className="px-6 py-4 font-semibold text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-dark-700/50">
              {filtered.length === 0 ? (
                <tr>
                  <td colSpan="6" className="px-6 py-12 text-center text-gray-500">
                    No employees matching filter criteria found.
                  </td>
                </tr>
              ) : (
                filtered.map((emp) => (
                  <tr key={emp.employee_id} className="hover:bg-dark-700/20 transition-colors">
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-full bg-dark-700 overflow-hidden border border-dark-600 flex items-center justify-center font-bold text-white">
                          {emp.photo_path ? (
                            <img src={`http://localhost:8000${emp.photo_path}`} alt="" className="w-full h-full object-cover" />
                          ) : (
                            emp.name.charAt(0)
                          )}
                        </div>
                        <div>
                          <div className="font-semibold text-white">{emp.name}</div>
                          <div className="text-xs text-gray-400">{emp.employee_id}</div>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-gray-300 font-medium">
                      {emp.department}
                    </td>
                    <td className="px-6 py-4">
                      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-blue-500/10 text-blue-400 border border-blue-500/20 text-xs font-semibold">
                        <Shield className="w-3.5 h-3.5" />
                        <span>Level {emp.access_level}</span>
                      </span>
                    </td>
                    <td className="px-6 py-4 text-xs">
                      <div className="flex items-center gap-2">
                        <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded font-medium ${emp.has_face_profile ? 'bg-emerald-500/10 text-emerald-400' : 'bg-gray-800 text-gray-500'}`}>
                          {emp.has_face_profile && <Check className="w-3 h-3" />} Face (512-dim)
                        </span>
                        <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded font-medium ${emp.has_body_profile ? 'bg-indigo-500/10 text-indigo-400' : 'bg-gray-800 text-gray-500'}`}>
                          {emp.has_body_profile && <Check className="w-3 h-3" />} Body (256-dim)
                        </span>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold ${emp.is_active ? 'bg-emerald-500/10 text-emerald-400' : 'bg-red-500/10 text-red-400'}`}>
                        {emp.is_active ? 'Active' : 'Deactivated'}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-right">
                      {emp.is_active && (
                        <button
                          onClick={() => handleDeactivate(emp.employee_id)}
                          title="Deactivate Access"
                          className="p-1.5 rounded-lg text-gray-400 hover:text-red-400 hover:bg-red-500/10 transition-colors"
                        >
                          <UserX className="w-4 h-4" />
                        </button>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
