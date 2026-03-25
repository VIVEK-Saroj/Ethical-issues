import { useEffect, useState } from 'react';
import {
  TrendingUp, TrendingDown, Minus, Search, Play, BarChart3,
} from 'lucide-react';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Area, AreaChart, Legend,
} from 'recharts';
import api from '../api/client';
import Card from '../components/ui/Card';
import Badge from '../components/ui/Badge';
import Button from '../components/ui/Button';
import Spinner from '../components/ui/Spinner';
import { useAuth } from '../context/AuthContext';
import type { ForecastSummary, Forecast } from '../types';
import toast from 'react-hot-toast';

export default function ForecastPage() {
  const { user } = useAuth();
  const [summaries, setSummaries] = useState<ForecastSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);
  const [search, setSearch] = useState('');
  const [selectedSku, setSelectedSku] = useState<string | null>(null);
  const [skuForecasts, setSkuForecasts] = useState<Forecast[]>([]);
  const [skuLoading, setSkuLoading] = useState(false);

  useEffect(() => {
    api.get('/forecasts/summary/all')
      .then(({ data }) => setSummaries(data))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const runForecasts = async () => {
    setRunning(true);
    try {
      const { data } = await api.post('/forecasts/run');
      toast.success(data.message);
      // Refresh summaries
      const res = await api.get('/forecasts/summary/all');
      setSummaries(res.data);
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Failed to run forecasts');
    } finally {
      setRunning(false);
    }
  };

  const viewSkuForecast = async (sku: string) => {
    setSelectedSku(sku);
    setSkuLoading(true);
    try {
      const { data } = await api.get(`/forecasts/${sku}?days=7`);
      setSkuForecasts(data);
    } catch {
      setSkuForecasts([]);
    } finally {
      setSkuLoading(false);
    }
  };

  const TrendIcon = ({ trend }: { trend: string }) => {
    if (trend === 'up') return <TrendingUp size={14} className="text-emerald-500" />;
    if (trend === 'down') return <TrendingDown size={14} className="text-red-500" />;
    return <Minus size={14} className="text-gray-400" />;
  };

  const filtered = summaries.filter(
    (s) =>
      s.product_name.toLowerCase().includes(search.toLowerCase()) ||
      s.sku.toLowerCase().includes(search.toLowerCase()) ||
      s.category.toLowerCase().includes(search.toLowerCase())
  );

  const chartData = skuForecasts.map((fc) => ({
    date: fc.forecast_date.slice(5),
    demand: fc.predicted_demand,
    lower: fc.lower_bound,
    upper: fc.upper_bound,
  }));

  const selectedSummary = summaries.find((s) => s.sku === selectedSku);

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Demand Forecasts</h1>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
            AI-powered SKU-level demand predictions
          </p>
        </div>
        <div className="flex items-center gap-3">
          <div className="relative">
            <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
            <input
              type="text"
              placeholder="Search SKU or product..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-9 pr-4 py-2.5 rounded-xl border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900 text-sm text-gray-900 dark:text-white focus:ring-2 focus:ring-brand-500 outline-none w-64"
            />
          </div>
          {user?.role === 'admin' && (
            <Button onClick={runForecasts} loading={running}>
              <Play size={14} className="mr-2" />
              Run Forecasts
            </Button>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Forecast chart */}
        <div className="lg:col-span-2">
          <Card>
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-semibold text-gray-900 dark:text-white">
                {selectedSku ? `Forecast — ${selectedSummary?.product_name || selectedSku}` : 'Select a product to view forecast'}
              </h3>
              {selectedSku && (
                <Badge variant="info">{selectedSku}</Badge>
              )}
            </div>

            {!selectedSku ? (
              <div className="flex flex-col items-center justify-center py-16 text-gray-400">
                <BarChart3 size={48} className="mb-4 text-gray-300 dark:text-gray-700" />
                <p className="text-sm">Click on a product below to see its forecast</p>
              </div>
            ) : skuLoading ? (
              <div className="flex justify-center py-16"><Spinner /></div>
            ) : chartData.length === 0 ? (
              <div className="text-center py-16 text-gray-400">
                <p className="text-sm">No forecast data for this SKU</p>
                <p className="text-xs mt-1">Run forecasts to generate predictions</p>
              </div>
            ) : (
              <div className="h-72">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={chartData}>
                    <defs>
                      <linearGradient id="demandGrad" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.2} />
                        <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                      </linearGradient>
                      <linearGradient id="bandGrad" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#93c5fd" stopOpacity={0.15} />
                        <stop offset="95%" stopColor="#93c5fd" stopOpacity={0} />
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
                    <Area type="monotone" dataKey="upper" stroke="transparent" fill="url(#bandGrad)" name="Upper Bound" />
                    <Area type="monotone" dataKey="lower" stroke="transparent" fill="transparent" name="Lower Bound" />
                    <Area type="monotone" dataKey="demand" stroke="#3b82f6" fill="url(#demandGrad)" strokeWidth={2.5} name="Predicted Demand" />
                    <Legend formatter={(value) => <span className="text-xs text-gray-500">{value}</span>} />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            )}

            {selectedSummary && (
              <div className="grid grid-cols-3 gap-3 mt-4">
                <div className="p-3 rounded-xl bg-blue-50 dark:bg-blue-950/20 text-center">
                  <p className="text-lg font-bold text-blue-600">{selectedSummary.avg_daily_sales.toFixed(0)}</p>
                  <p className="text-[10px] text-blue-500">Avg Daily Sales</p>
                </div>
                <div className="p-3 rounded-xl bg-emerald-50 dark:bg-emerald-950/20 text-center">
                  <p className="text-lg font-bold text-emerald-600">{selectedSummary.predicted_tomorrow.toFixed(0)}</p>
                  <p className="text-[10px] text-emerald-500">Tomorrow</p>
                </div>
                <div className="p-3 rounded-xl bg-violet-50 dark:bg-violet-950/20 text-center">
                  <p className="text-lg font-bold text-violet-600">{selectedSummary.predicted_next_week.toFixed(0)}</p>
                  <p className="text-[10px] text-violet-500">Next 7 Days</p>
                </div>
              </div>
            )}
          </Card>
        </div>

        {/* Product list */}
        <Card className="overflow-hidden" padding={false}>
          <div className="px-6 pt-6 pb-3">
            <h3 className="text-sm font-semibold text-gray-900 dark:text-white">Products</h3>
            <p className="text-xs text-gray-400 mt-0.5">{filtered.length} products</p>
          </div>
          {loading ? (
            <div className="flex justify-center py-12"><Spinner /></div>
          ) : (
            <div className="max-h-[500px] overflow-y-auto divide-y divide-gray-100 dark:divide-gray-800">
              {filtered.map((s) => (
                <button
                  key={s.sku}
                  onClick={() => viewSkuForecast(s.sku)}
                  className={`w-full text-left px-6 py-3 hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors ${
                    selectedSku === s.sku ? 'bg-brand-50 dark:bg-brand-950/20 border-l-2 border-brand-500' : ''
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div className="min-w-0">
                      <p className="text-sm font-medium text-gray-900 dark:text-white truncate">{s.product_name}</p>
                      <p className="text-xs text-gray-500">{s.sku} · {s.category}</p>
                    </div>
                    <div className="flex items-center gap-2 ml-2">
                      <TrendIcon trend={s.trend} />
                      <span className="text-sm font-semibold text-gray-700 dark:text-gray-300">
                        {s.predicted_tomorrow.toFixed(0)}
                      </span>
                    </div>
                  </div>
                </button>
              ))}
            </div>
          )}
        </Card>
      </div>
    </div>
  );
}
