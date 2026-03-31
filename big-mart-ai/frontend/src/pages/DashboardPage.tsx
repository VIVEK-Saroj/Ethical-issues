import { useEffect, useState } from 'react';
import { Package, Camera, AlertTriangle, TrendingUp, ArrowUpRight, ArrowDownRight } from 'lucide-react';
import {
  PieChart, Pie, Cell, AreaChart, Area, BarChart, Bar,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend,
} from 'recharts';
import api from '../api/client';
import Card from '../components/ui/Card';
import Badge from '../components/ui/Badge';
import { CardSkeleton, ChartSkeleton } from '../components/ui/Skeleton';
import type { DashboardStats, RiskDistribution, TopRiskProduct, RecentScan, TrendPoint } from '../types';

const RISK_COLORS = { critical: '#ef4444', warning: '#f59e0b', ok: '#10b981' };

export default function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [risk, setRisk] = useState<RiskDistribution | null>(null);
  const [topRisk, setTopRisk] = useState<TopRiskProduct[]>([]);
  const [recentScans, setRecentScans] = useState<RecentScan[]>([]);
  const [salesTrend, setSalesTrend] = useState<TrendPoint[]>([]);
  const [forecastTrend, setForecastTrend] = useState<TrendPoint[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      api.get('/dashboard/stats'),
      api.get('/dashboard/risk-distribution'),
      api.get('/dashboard/top-risk'),
      api.get('/dashboard/recent-scans'),
      api.get('/dashboard/sales-trend?days=14'),
      api.get('/dashboard/forecast-trend?days=7'),
    ])
      .then(([s, r, t, sc, st, ft]) => {
        setStats(s.data);
        setRisk(r.data);
        setTopRisk(t.data);
        setRecentScans(sc.data);
        setSalesTrend(st.data);
        setForecastTrend(ft.data);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {Array.from({ length: 4 }).map((_, i) => <CardSkeleton key={i} />)}
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <ChartSkeleton />
          <ChartSkeleton />
        </div>
      </div>
    );
  }

  const kpiCards = [
    { label: 'Total Products', value: stats?.total_products ?? 0, icon: Package, color: 'text-brand-600 bg-brand-50 dark:bg-brand-950/30', change: '+3 this week' },
    { label: 'Scans Today', value: stats?.scans_today ?? 0, icon: Camera, color: 'text-violet-600 bg-violet-50 dark:bg-violet-950/30', change: 'Updated live' },
    { label: 'Stock-out Risks', value: stats?.stockout_risks ?? 0, icon: AlertTriangle, color: 'text-red-600 bg-red-50 dark:bg-red-950/30', change: 'Needs attention', negative: true },
    { label: 'Forecast Accuracy', value: `${stats?.forecast_accuracy ?? 0}%`, icon: TrendingUp, color: 'text-emerald-600 bg-emerald-50 dark:bg-emerald-950/30', change: 'Last 7 days' },
  ];

  const pieData = risk ? [
    { name: 'Critical', value: risk.critical, color: RISK_COLORS.critical },
    { name: 'Warning', value: risk.warning, color: RISK_COLORS.warning },
    { name: 'OK', value: risk.ok, color: RISK_COLORS.ok },
  ] : [];

  // Merge sales + forecast for area chart
  const combinedTrend = [
    ...salesTrend.map((s) => ({ date: s.date.slice(5), sales: s.value, forecast: null as number | null })),
    ...forecastTrend.map((f) => ({ date: f.date.slice(5), sales: null as number | null, forecast: f.value })),
  ];

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Dashboard</h1>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">Overview of your store's shelf intelligence</p>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {kpiCards.map(({ label, value, icon: Icon, color, change, negative }) => (
          <Card key={label} hover>
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm font-medium text-gray-500 dark:text-gray-400">{label}</p>
                <p className="text-3xl font-bold text-gray-900 dark:text-white mt-1">{value}</p>
                <div className="flex items-center gap-1 mt-2">
                  {negative ? (
                    <ArrowUpRight size={14} className="text-red-500" />
                  ) : (
                    <ArrowUpRight size={14} className="text-emerald-500" />
                  )}
                  <span className="text-xs text-gray-500 dark:text-gray-400">{change}</span>
                </div>
              </div>
              <div className={`p-3 rounded-xl ${color}`}>
                <Icon size={22} />
              </div>
            </div>
          </Card>
        ))}
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Risk Distribution Pie */}
        <Card>
          <h3 className="text-sm font-semibold text-gray-900 dark:text-white mb-4">Stock Risk Distribution</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={pieData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={100}
                  paddingAngle={4}
                  dataKey="value"
                >
                  {pieData.map((entry) => (
                    <Cell key={entry.name} fill={entry.color} strokeWidth={0} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#1f2937',
                    border: 'none',
                    borderRadius: '12px',
                    color: '#fff',
                    fontSize: '13px',
                  }}
                />
                <Legend
                  verticalAlign="bottom"
                  iconType="circle"
                  formatter={(value) => <span className="text-sm text-gray-600 dark:text-gray-400">{value}</span>}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </Card>

        {/* Sales vs Forecast Area Chart */}
        <Card>
          <h3 className="text-sm font-semibold text-gray-900 dark:text-white mb-4">Sales vs Forecast Trend</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={combinedTrend}>
                <defs>
                  <linearGradient id="salesGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="forecastGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#10b981" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis dataKey="date" tick={{ fontSize: 11, fill: '#9ca3af' }} />
                <YAxis tick={{ fontSize: 11, fill: '#9ca3af' }} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#1f2937',
                    border: 'none',
                    borderRadius: '12px',
                    color: '#fff',
                    fontSize: '13px',
                  }}
                />
                <Area type="monotone" dataKey="sales" stroke="#3b82f6" fillOpacity={1} fill="url(#salesGrad)" strokeWidth={2} name="Actual Sales" connectNulls={false} />
                <Area type="monotone" dataKey="forecast" stroke="#10b981" fillOpacity={1} fill="url(#forecastGrad)" strokeWidth={2} strokeDasharray="6 3" name="Forecast" connectNulls={false} />
                <Legend iconType="line" formatter={(value) => <span className="text-xs text-gray-500">{value}</span>} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </Card>
      </div>

      {/* Bottom Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Top At-Risk Products */}
        <Card>
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold text-gray-900 dark:text-white">Top At-Risk Products</h3>
            <a href="/alerts" className="text-xs text-brand-600 hover:underline">View all →</a>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-100 dark:border-gray-800">
                  <th className="text-left py-2 font-medium text-gray-500 dark:text-gray-400">Product</th>
                  <th className="text-right py-2 font-medium text-gray-500 dark:text-gray-400">Stock</th>
                  <th className="text-right py-2 font-medium text-gray-500 dark:text-gray-400">Demand</th>
                  <th className="text-right py-2 font-medium text-gray-500 dark:text-gray-400">Risk</th>
                </tr>
              </thead>
              <tbody>
                {topRisk.map((p) => (
                  <tr key={p.product_id} className="border-b border-gray-50 dark:border-gray-800/50">
                    <td className="py-3">
                      <p className="font-medium text-gray-900 dark:text-white">{p.name}</p>
                      <p className="text-xs text-gray-500">{p.sku}</p>
                    </td>
                    <td className="text-right text-gray-700 dark:text-gray-300">{p.shelf_stock}</td>
                    <td className="text-right text-gray-700 dark:text-gray-300">{p.predicted_demand.toFixed(0)}</td>
                    <td className="text-right">
                      <Badge variant={p.risk_level === 'critical' ? 'danger' : 'warning'} dot>
                        {p.risk_level}
                      </Badge>
                    </td>
                  </tr>
                ))}
                {topRisk.length === 0 && (
                  <tr>
                    <td colSpan={4} className="text-center py-8 text-gray-400">No at-risk products</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </Card>

        {/* Recent Scans */}
        <Card>
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold text-gray-900 dark:text-white">Recent Shelf Scans</h3>
            <a href="/shelf-analysis" className="text-xs text-brand-600 hover:underline">View all →</a>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
            {recentScans.map((scan) => (
              <a
                key={scan.id}
                href={`/shelf-analysis?id=${scan.id}`}
                className="group rounded-xl overflow-hidden border border-gray-100 dark:border-gray-800 hover:border-brand-300 dark:hover:border-brand-700 transition-all"
              >
                <div className="aspect-video bg-gray-100 dark:bg-gray-800 relative overflow-hidden">
                  <img
                    src={scan.image_url}
                    alt={`Aisle ${scan.aisle}`}
                    className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                    loading="lazy"
                    referrerPolicy="no-referrer"
                    crossOrigin="anonymous"
                  />
                  <div className="absolute bottom-1 left-1">
                    <Badge variant="info">{scan.aisle}</Badge>
                  </div>
                </div>
                <div className="p-2">
                  <p className="text-xs font-medium text-gray-700 dark:text-gray-300">{scan.total_detections} items</p>
                  <p className="text-[10px] text-gray-400">{scan.shelf_occupancy}% occupancy</p>
                </div>
              </a>
            ))}
            {recentScans.length === 0 && (
              <div className="col-span-full text-center py-8 text-gray-400 text-sm">No scans yet</div>
            )}
          </div>
        </Card>
      </div>
    </div>
  );
}
