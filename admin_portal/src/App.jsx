import React, { useState, useEffect } from 'react';
import { api } from './api';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import AddEmployee from './pages/AddEmployee';
import EmployeeList from './pages/EmployeeList';
import MultiCameraGrid from './pages/MultiCameraGrid';
import CameraManagement from './pages/CameraManagement';
import CameraHealth from './pages/CameraHealth';
import CrossCamera from './pages/CrossCamera';
import AccessLogs from './pages/AccessLogs';

import {
  LayoutDashboard,
  Video,
  UserPlus,
  Users,
  Camera,
  Activity,
  GitFork,
  FileText,
  LogOut,
  Shield,
  ExternalLink
} from 'lucide-react';

export default function App() {
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [user, setUser] = useState(api.getUser());
  const [activeTab, setActiveTab] = useState('dashboard');

  const handleLoginSuccess = () => {
    setToken(localStorage.getItem('token'));
    setUser(api.getUser());
    setActiveTab('dashboard');
  };

  const handleLogout = () => {
    api.logout();
    setToken(null);
    setUser(null);
  };

  if (!token) {
    return <Login onLoginSuccess={handleLoginSuccess} />;
  }

  const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { id: 'multi-camera', label: 'Live Camera Wall', icon: Video },
    { id: 'add-employee', label: 'Enroll Employee', icon: UserPlus },
    { id: 'employees', label: 'Employee Directory', icon: Users },
    { id: 'cameras', label: 'Cameras & Zones', icon: Camera },
    { id: 'health', label: 'Camera Health', icon: Activity },
    { id: 'cross-camera', label: 'Cross-Camera Tracking', icon: GitFork },
    { id: 'logs', label: 'Access Audit Logs', icon: FileText },
  ];

  return (
    <div className="min-h-screen bg-dark-900 flex text-gray-100 font-sans">
      {/* Sidebar */}
      <aside className="w-64 bg-dark-800 border-r border-dark-700 flex flex-col justify-between shrink-0">
        <div>
          {/* Brand Logo */}
          <div className="p-6 border-b border-dark-700 flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-blue-600/10 border border-blue-500/20 flex items-center justify-center text-blue-500">
              <Shield className="w-5 h-5" />
            </div>
            <div>
              <h1 className="font-bold text-white text-sm tracking-tight leading-tight">AI Access Guard</h1>
              <p className="text-xs text-gray-400">Admin Control Center</p>
            </div>
          </div>

          {/* Nav List */}
          <nav className="p-4 space-y-1.5">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = activeTab === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => setActiveTab(item.id)}
                  className={`w-full flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-sm font-medium transition-all ${
                    isActive
                      ? 'bg-blue-600 text-white shadow-lg shadow-blue-600/20'
                      : 'text-gray-400 hover:text-white hover:bg-dark-700/50'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  <span>{item.label}</span>
                </button>
              );
            })}
          </nav>
        </div>

        {/* Bottom Sidebar: Kiosk Link & User info */}
        <div className="p-4 border-t border-dark-700 space-y-3">
          <a
            href="http://localhost:8000/camera"
            target="_blank"
            rel="noopener noreferrer"
            className="w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl bg-dark-900 border border-dark-700 hover:border-dark-600 text-xs font-semibold text-gray-300 hover:text-white transition-colors"
          >
            <span>Live Door Kiosk</span>
            <ExternalLink className="w-3.5 h-3.5 text-blue-400" />
          </a>

          <div className="flex items-center justify-between pt-2">
            <div className="min-w-0">
              <div className="text-sm font-semibold text-white truncate">{user?.username || 'Admin'}</div>
              <div className="text-xs text-blue-400 uppercase font-semibold">{user?.role || 'admin'}</div>
            </div>
            <button
              onClick={handleLogout}
              title="Sign Out"
              className="p-2 text-gray-400 hover:text-red-400 hover:bg-red-500/10 rounded-lg transition-colors"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 flex flex-col min-w-0 overflow-y-auto">
        {/* Top Header */}
        <header className="h-16 bg-dark-800/80 backdrop-blur border-b border-dark-700 px-8 flex items-center justify-between sticky top-0 z-10">
          <div className="text-sm text-gray-400">
            System Status: <span className="text-emerald-400 font-semibold font-mono">● LIVE</span>
          </div>
          <div className="text-xs text-gray-400 font-medium">
            IBM National Hackathon 2026 &bull; Secure Redis Stack
          </div>
        </header>

        {/* Page View */}
        <div className="p-8">
          {activeTab === 'dashboard' && <Dashboard onNavigate={(tab) => setActiveTab(tab)} />}
          {activeTab === 'multi-camera' && <MultiCameraGrid />}
          {activeTab === 'add-employee' && <AddEmployee onEmployeeAdded={() => setActiveTab('employees')} />}
          {activeTab === 'employees' && <EmployeeList />}
          {activeTab === 'cameras' && <CameraManagement />}
          {activeTab === 'health' && <CameraHealth />}
          {activeTab === 'cross-camera' && <CrossCamera />}
          {activeTab === 'logs' && <AccessLogs />}
        </div>
      </main>
    </div>
  );
}
