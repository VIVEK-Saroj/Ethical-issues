import { useEffect, useState } from 'react';
import { AlertTriangle, ShieldAlert, ShieldCheck, Search, Filter, Package } from 'lucide-react';
import api from '../api/client';
import Card from '../components/ui/Card';
import Badge from '../components/ui/Badge';
import Spinner from '../components/ui/Spinner';
import type { Alert, AlertSummary } from '../types';

export default function AlertsPage() {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [summary, setSummary] = useState<AlertSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [riskFilter, setRiskFilter] = useState<string>('');

  useEffect(() => {
    Promise.all([api.get('/alerts/'), api.get('/alerts/summary')])
      .then(([a, s]) => {
        setAlerts(a.data);
        setSummary(s.data);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const filtered = alerts.filter((a) => {
    const matchesSearch =
      a.product_name.toLowerCase().includes(search.toLowerCase()) ||
      a.sku.toLowerCase().includes(search.toLowerCase()) ||
      a.category.toLowerCase().includes(search.toLowerCase());
    const matchesRisk = !riskFilter || a.risk_level === riskFilter;
    return matchesSearch && matchesRisk;
  });

  const summaryCards = [
    {
      label: 'Critical',
      value: summary?.critical ?? 0,
      icon: ShieldAlert,
      color: 'text-red-600',
      bgColor: 'bg-red-50 dark:bg-red-950/20 border-red-200 dark:border-red-800',
      description: 'Stock < 1 day demand',
    },
    {
      label: 'Warning',
      value: summary?.warning ?? 0,
      icon: AlertTriangle,
      color: 'text-amber-600',
      bgColor: 'bg-amber-50 dark:bg-amber-950/20 border-amber-200 dark:border-amber-800',
      description: 'Stock < 3 days demand',
    },
    {
      label: 'OK',
      value: summary?.ok ?? 0,
      icon: ShieldCheck,
      color: 'text-emerald-600',
      bgColor: 'bg-emerald-50 dark:bg-emerald-950/20 border-emerald-200 dark:border-emerald-800',
      description: 'Sufficient stock',
    },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Stock Alerts</h1>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
          Products at risk of stock-out with restocking suggestions
        </p>
      </div>

      {/* Summary cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {summaryCards.map(({ label, value, icon: Icon, color, bgColor, description }) => (
          <button
            key={label}
            onClick={() => setRiskFilter(riskFilter === label.toLowerCase() ? '' : label.toLowerCase())}
            className={`p-5 rounded-2xl border text-left transition-all ${bgColor} ${
              riskFilter === label.toLowerCase() ? 'ring-2 ring-offset-2 ring-brand-500' : ''
            }`}
          >
            <div className="flex items-start justify-between">
              <div>
                <p className={`text-3xl font-bold ${color}`}>{value}</p>
                <p className="text-sm font-semibold text-gray-900 dark:text-white mt-1">{label}</p>
                <p className="text-xs text-gray-500 mt-0.5">{description}</p>
              </div>
              <Icon size={28} className={color} />
            </div>
          </button>
        ))}
      </div>

      {/* Search */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
          <input
            type="text"
            placeholder="Search products, SKUs, or categories..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-4 py-2.5 rounded-xl border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900 text-sm text-gray-900 dark:text-white focus:ring-2 focus:ring-brand-500 outline-none"
          />
        </div>
        {riskFilter && (
          <button
            onClick={() => setRiskFilter('')}
            className="px-3 py-2 rounded-xl bg-gray-100 dark:bg-gray-800 text-sm text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors"
          >
            Clear filter ×
          </button>
        )}
      </div>

      {/* Alerts table */}
      {loading ? (
        <div className="flex justify-center py-20"><Spinner size="lg" /></div>
      ) : (
        <Card padding={false}>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-200 dark:border-gray-800 bg-gray-50 dark:bg-gray-900/50">
                  <th className="text-left px-6 py-3 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">Product</th>
                  <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">Category</th>
                  <th className="text-right px-4 py-3 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">Shelf Stock</th>
                  <th className="text-right px-4 py-3 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">7d Demand</th>
                  <th className="text-center px-4 py-3 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">Risk</th>
                  <th className="text-right px-6 py-3 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">Restock Qty</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 dark:divide-gray-800">
                {filtered.map((alert) => (
                  <tr
                    key={alert.product_id}
                    className="hover:bg-gray-50 dark:hover:bg-gray-800/30 transition-colors"
                  >
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-3">
                        <div className="w-9 h-9 rounded-lg bg-gray-100 dark:bg-gray-800 flex items-center justify-center flex-shrink-0">
                          <Package size={16} className="text-gray-400" />
                        </div>
                        <div>
                          <p className="text-sm font-medium text-gray-900 dark:text-white">{alert.product_name}</p>
                          <p className="text-xs text-gray-500">{alert.sku}</p>
                        </div>
                      </div>
                    </td>
                    <td className="px-4 py-4">
                      <Badge variant="default">{alert.category}</Badge>
                    </td>
                    <td className="px-4 py-4 text-right">
                      <span className={`text-sm font-semibold ${alert.shelf_stock < 5 ? 'text-red-600' : 'text-gray-900 dark:text-white'}`}>
                        {alert.shelf_stock}
                      </span>
                    </td>
                    <td className="px-4 py-4 text-right text-sm text-gray-700 dark:text-gray-300">
                      {alert.predicted_demand_7d.toFixed(0)}
                    </td>
                    <td className="px-4 py-4 text-center">
                      <Badge
                        variant={
                          alert.risk_level === 'critical'
                            ? 'danger'
                            : alert.risk_level === 'warning'
                            ? 'warning'
                            : 'success'
                        }
                        dot
                      >
                        {alert.risk_level}
                      </Badge>
                    </td>
                    <td className="px-6 py-4 text-right">
                      {alert.restock_qty > 0 ? (
                        <span className="inline-flex items-center gap-1 px-3 py-1 rounded-lg bg-brand-50 dark:bg-brand-950/20 text-brand-700 dark:text-brand-400 text-sm font-semibold">
                          +{alert.restock_qty}
                        </span>
                      ) : (
                        <span className="text-sm text-gray-400">—</span>
                      )}
                    </td>
                  </tr>
                ))}
                {filtered.length === 0 && (
                  <tr>
                    <td colSpan={6} className="text-center py-12 text-gray-400">
                      {search || riskFilter ? 'No matching alerts' : 'No alerts to display'}
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </Card>
      )}
    </div>
  );
}
