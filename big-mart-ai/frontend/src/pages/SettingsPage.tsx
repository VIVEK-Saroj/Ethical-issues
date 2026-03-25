import { useState } from 'react';
import { Settings as SettingsIcon, Sun, Moon, Store, Database, Bug } from 'lucide-react';
import Card from '../components/ui/Card';
import Button from '../components/ui/Button';
import Badge from '../components/ui/Badge';
import { useAuth } from '../context/AuthContext';
import toast from 'react-hot-toast';
import api from '../api/client';

export default function SettingsPage() {
  const { user } = useAuth();
  const [dark, setDark] = useState(document.documentElement.classList.contains('dark'));

  const toggleDark = () => {
    document.documentElement.classList.toggle('dark');
    setDark(!dark);
  };

  const checkHealth = async () => {
    try {
      const { data } = await api.get('/health');
      toast.success(`Backend: ${data.status} (${data.service})`);
    } catch {
      toast.error('Backend unreachable');
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Settings</h1>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">System configuration and preferences</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* User info */}
        <Card>
          <h3 className="text-sm font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
            <Store size={16} />
            Account
          </h3>
          <div className="space-y-3">
            <div className="flex justify-between text-sm">
              <span className="text-gray-500">Username</span>
              <span className="font-medium text-gray-900 dark:text-white">{user?.username}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-gray-500">Email</span>
              <span className="font-medium text-gray-900 dark:text-white">{user?.email}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-gray-500">Role</span>
              <Badge variant={user?.role === 'admin' ? 'info' : 'default'}>{user?.role}</Badge>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-gray-500">Store</span>
              <span className="font-medium text-gray-900 dark:text-white">{user?.store_id}</span>
            </div>
          </div>
        </Card>

        {/* Appearance */}
        <Card>
          <h3 className="text-sm font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
            {dark ? <Moon size={16} /> : <Sun size={16} />}
            Appearance
          </h3>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-900 dark:text-white">Dark Mode</p>
              <p className="text-xs text-gray-500">Toggle dark/light theme</p>
            </div>
            <button
              onClick={toggleDark}
              className={`relative w-12 h-6 rounded-full transition-colors ${dark ? 'bg-brand-600' : 'bg-gray-300'}`}
            >
              <span
                className={`absolute top-0.5 w-5 h-5 rounded-full bg-white shadow transition-transform ${dark ? 'translate-x-6' : 'translate-x-0.5'}`}
              />
            </button>
          </div>
        </Card>

        {/* System */}
        <Card>
          <h3 className="text-sm font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
            <Database size={16} />
            System
          </h3>
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-900 dark:text-white">Backend Health</p>
                <p className="text-xs text-gray-500">Check API connectivity</p>
              </div>
              <Button size="sm" variant="secondary" onClick={checkHealth}>
                <Bug size={14} className="mr-1.5" />
                Test
              </Button>
            </div>
          </div>
        </Card>

        {/* About */}
        <Card>
          <h3 className="text-sm font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
            <SettingsIcon size={16} />
            About
          </h3>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-500">Version</span>
              <span className="font-medium text-gray-900 dark:text-white">1.0.0</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">ML Models</span>
              <span className="font-medium text-gray-900 dark:text-white">YOLOv8n + Prophet</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">Stack</span>
              <span className="font-medium text-gray-900 dark:text-white">React + FastAPI</span>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
}
