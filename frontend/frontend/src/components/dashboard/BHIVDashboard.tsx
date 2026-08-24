import React, { useState, useEffect, useCallback } from 'react';
import { apiService } from '../../services/api';

interface EcosystemProduct {
  product_name: string;
  protocol: string;
  capabilities: string[];
  auth_type: string;
  timeout_seconds: number;
  rate_limit_per_minute: number;
  event_topics: string[];
  version: string;
}

interface IntegrationHealth {
  product: string;
  status: 'healthy' | 'degraded' | 'unhealthy' | 'unknown';
  last_check: string | null;
  last_success: string | null;
  last_error: string | null;
  error_count: number;
  success_count: number;
  avg_latency_ms: number;
}

interface SystemMetrics {
  uptime: { seconds: number; hours: number };
  requests: { total: number; errors: number; success_rate: number };
  enforcement: { allows: number; blocks: number; rewrites: number; total: number };
}

const STATUS_COLORS: Record<string, string> = {
  healthy: '#22c55e',
  degraded: '#f59e0b',
  unhealthy: '#ef4444',
  unknown: '#6b7280',
};

const PRODUCT_ICONS: Record<string, string> = {
  UniGuru: '📚',
  SETU: '🔗',
  Gurukul: '🎓',
  Samruddhi: '🌱',
  NamamiGange: '🌊',
  SVACS: '🎖️',
  UCCIS: '📢',
  NYAI: '🤖',
  Brahmanda: '🌐',
  Bucket: '🪣',
  TANTRA: '⚙️',
};

export const BHIVDashboard: React.FC = () => {
  const [products, setProducts] = useState<string[]>([]);
  const [manifests, setManifests] = useState<Record<string, EcosystemProduct>>({});
  const [health, setHealth] = useState<Record<string, IntegrationHealth>>({});
  const [metrics, setMetrics] = useState<SystemMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    try {
      const [productsRes, manifestsRes, healthRes, metricsRes] = await Promise.allSettled([
        fetch(`${process.env.REACT_APP_API_URL}/api/ecosystem/products`, {
          headers: { 'X-API-Key': process.env.REACT_APP_API_KEY || '' },
        }).then(r => r.json()),
        fetch(`${process.env.REACT_APP_API_URL}/api/ecosystem/manifests`, {
          headers: { 'X-API-Key': process.env.REACT_APP_API_KEY || '' },
        }).then(r => r.json()),
        fetch(`${process.env.REACT_APP_API_URL}/api/ecosystem/health`, {
          headers: { 'X-API-Key': process.env.REACT_APP_API_KEY || '' },
        }).then(r => r.json()),
        fetch(`${process.env.REACT_APP_API_URL}/api/metrics`, {
          headers: { 'X-API-Key': process.env.REACT_APP_API_KEY || '' },
        }).then(r => r.json()),
      ]);

      if (productsRes.status === 'fulfilled') setProducts(productsRes.value.products || []);
      if (manifestsRes.status === 'fulfilled') setManifests(manifestsRes.value.manifests || {});
      if (healthRes.status === 'fulfilled') setHealth(healthRes.value.integrations || {});
      if (metricsRes.status === 'fulfilled') setMetrics(metricsRes.value);
      setError(null);
    } catch (e) {
      setError('Failed to fetch dashboard data');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, [fetchData]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-white">BHIV Ecosystem Dashboard</h1>
          <p className="text-gray-400 mt-1">Mitra Integration Overview</p>
        </div>
        <button
          onClick={fetchData}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
        >
          Refresh
        </button>
      </div>

      {error && (
        <div className="bg-red-900/30 border border-red-500 rounded-lg p-4 mb-6 text-red-300">
          {error}
        </div>
      )}

      {/* KPI Cards */}
      <div className="grid grid-cols-4 gap-4 mb-8">
        <KpiCard
          title="Total Products"
          value={products.length.toString()}
          icon="🏢"
          color="blue"
        />
        <KpiCard
          title="Healthy Integrations"
          value={Object.values(health).filter(h => h.status === 'healthy').length.toString()}
          icon="✅"
          color="green"
        />
        <KpiCard
          title="Request Success Rate"
          value={`${metrics?.requests?.success_rate || 0}%`}
          icon="📊"
          color="purple"
        />
        <KpiCard
          title="Uptime"
          value={`${Math.round((metrics?.uptime?.hours || 0))}h`}
          icon="⏱️"
          color="amber"
        />
      </div>

      {/* Product Grid */}
      <div className="mb-8">
        <h2 className="text-lg font-semibold text-white mb-4">BHIV Products</h2>
        <div className="grid grid-cols-3 gap-4">
          {products.map(product => (
            <ProductCard
              key={product}
              product={product}
              manifest={manifests[product]}
              health={health[product]}
            />
          ))}
        </div>
      </div>

      {/* Enforcement & Metrics */}
      <div className="grid grid-cols-2 gap-6">
        <div className="bg-gray-800/50 rounded-xl p-6 border border-gray-700">
          <h3 className="text-lg font-semibold text-white mb-4">Enforcement Decisions</h3>
          <div className="space-y-3">
            <MetricBar label="Allows" value={metrics?.enforcement?.allows || 0} total={metrics?.enforcement?.total || 1} color="green" />
            <MetricBar label="Blocks" value={metrics?.enforcement?.blocks || 0} total={metrics?.enforcement?.total || 1} color="red" />
            <MetricBar label="Rewrites" value={metrics?.enforcement?.rewrites || 0} total={metrics?.enforcement?.total || 1} color="yellow" />
          </div>
        </div>

        <div className="bg-gray-800/50 rounded-xl p-6 border border-gray-700">
          <h3 className="text-lg font-semibold text-white mb-4">System Health</h3>
          <div className="space-y-3">
            <div className="flex justify-between text-gray-300">
              <span>Total Requests</span>
              <span className="font-mono">{metrics?.requests?.total || 0}</span>
            </div>
            <div className="flex justify-between text-gray-300">
              <span>Errors</span>
              <span className="font-mono text-red-400">{metrics?.requests?.errors || 0}</span>
            </div>
            <div className="flex justify-between text-gray-300">
              <span>Uptime Hours</span>
              <span className="font-mono">{metrics?.uptime?.hours?.toFixed(1) || 0}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

const KpiCard: React.FC<{ title: string; value: string; icon: string; color: string }> = ({
  title, value, icon, color,
}) => {
  const colorMap: Record<string, string> = {
    blue: 'from-blue-600/20 to-blue-800/20 border-blue-500/30',
    green: 'from-green-600/20 to-green-800/20 border-green-500/30',
    purple: 'from-purple-600/20 to-purple-800/20 border-purple-500/30',
    amber: 'from-amber-600/20 to-amber-800/20 border-amber-500/30',
  };
  return (
    <div className={`bg-gradient-to-br ${colorMap[color]} rounded-xl p-5 border`}>
      <div className="flex items-center gap-3">
        <span className="text-2xl">{icon}</span>
        <div>
          <p className="text-gray-400 text-sm">{title}</p>
          <p className="text-2xl font-bold text-white">{value}</p>
        </div>
      </div>
    </div>
  );
};

const ProductCard: React.FC<{
  product: string;
  manifest?: EcosystemProduct;
  health?: IntegrationHealth;
}> = ({ product, manifest, health }) => {
  const statusColor = STATUS_COLORS[health?.status || 'unknown'];
  return (
    <div className="bg-gray-800/50 rounded-xl p-5 border border-gray-700 hover:border-gray-600 transition">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <span className="text-xl">{PRODUCT_ICONS[product] || '📦'}</span>
          <h3 className="font-semibold text-white">{product}</h3>
        </div>
        <div
          className="w-3 h-3 rounded-full"
          style={{ backgroundColor: statusColor }}
        />
      </div>
      <div className="space-y-2 text-sm text-gray-400">
        <div className="flex justify-between">
          <span>Protocol</span>
          <span className="text-gray-300">{manifest?.protocol || 'N/A'}</span>
        </div>
        <div className="flex justify-between">
          <span>Latency</span>
          <span className="text-gray-300">{health?.avg_latency_ms?.toFixed(0) || 0}ms</span>
        </div>
        <div className="flex justify-between">
          <span>Success</span>
          <span className="text-gray-300">{health?.success_count || 0}</span>
        </div>
        <div className="flex justify-between">
          <span>Errors</span>
          <span className="text-red-400">{health?.error_count || 0}</span>
        </div>
      </div>
      {manifest?.event_topics && manifest.event_topics.length > 0 && (
        <div className="mt-3 flex flex-wrap gap-1">
          {manifest.event_topics.slice(0, 3).map(topic => (
            <span key={topic} className="text-xs bg-gray-700 text-gray-300 px-2 py-1 rounded">
              {topic}
            </span>
          ))}
        </div>
      )}
    </div>
  );
};

const MetricBar: React.FC<{ label: string; value: number; total: number; color: string }> = ({
  label, value, total, color,
}) => {
  const pct = total > 0 ? (value / total) * 100 : 0;
  const colorMap: Record<string, string> = {
    green: 'bg-green-500',
    red: 'bg-red-500',
    yellow: 'bg-yellow-500',
  };
  return (
    <div>
      <div className="flex justify-between text-sm mb-1">
        <span className="text-gray-400">{label}</span>
        <span className="text-gray-300">{value} ({pct.toFixed(1)}%)</span>
      </div>
      <div className="h-2 bg-gray-700 rounded-full overflow-hidden">
        <div
          className={`h-full ${colorMap[color]} rounded-full transition-all duration-500`}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
};

export default BHIVDashboard;
