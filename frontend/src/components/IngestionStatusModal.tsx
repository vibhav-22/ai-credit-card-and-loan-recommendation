import React, { useState, useEffect } from 'react';
import { X, RefreshCw, Database, ShieldCheck, CheckCircle2, AlertTriangle, ExternalLink } from 'lucide-react';
import { api } from '../services/api';

interface IngestionStatusModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const IngestionStatusModal: React.FC<IngestionStatusModalProps> = ({
  isOpen,
  onClose,
}) => {
  const [statusData, setStatusData] = useState<any>(null);
  const [sources, setSources] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [ingesting, setIngesting] = useState(false);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [stat, src] = await Promise.all([
        api.getIngestionStatus(),
        fetch('/api/v1/ingestion/sources').then((r) => r.json()),
      ]);
      setStatusData(stat);
      setSources(src);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen) {
      fetchData();
    }
  }, [isOpen]);

  const handleTriggerIngestion = async () => {
    setIngesting(true);
    try {
      await api.triggerIngestion();
      await fetchData();
    } catch (err) {
      alert(`Ingestion failed: ${err}`);
    } finally {
      setIngesting(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/50 backdrop-blur-sm animate-fadeIn">
      <div className="bg-white rounded-2xl shadow-2xl border border-slate-200 w-full max-w-4xl max-h-[85vh] flex flex-col overflow-hidden">
        {/* Header */}
        <div className="p-5 border-b border-slate-100 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="p-1.5 rounded-lg bg-sky-50 text-sky-600">
              <Database className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-slate-900">
                Official Sources & Ingestion Monitor
              </h3>
              <p className="text-xs text-slate-500">
                Live inspection of official bank web sources, content hashes, and verification rates.
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-100"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Body */}
        <div className="p-5 overflow-auto space-y-6">
          {/* Stats Bar */}
          {statusData?.stats && (
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              <div className="p-3 bg-slate-50 rounded-xl border border-slate-100">
                <span className="text-[11px] font-medium text-slate-500 block">Total Ingested</span>
                <span className="text-lg font-bold text-slate-900">{statusData.stats.total_products} Products</span>
              </div>
              <div className="p-3 bg-emerald-50 rounded-xl border border-emerald-100">
                <span className="text-[11px] font-medium text-emerald-700 block">Verified Status</span>
                <span className="text-lg font-bold text-emerald-900">{statusData.stats.verified} Verified</span>
              </div>
              <div className="p-3 bg-sky-50 rounded-xl border border-sky-100">
                <span className="text-[11px] font-medium text-sky-700 block">Configured Sources</span>
                <span className="text-lg font-bold text-sky-900">{statusData.stats.configured_sources} Official Portals</span>
              </div>
              <div className="p-3 bg-amber-50 rounded-xl border border-amber-100">
                <span className="text-[11px] font-medium text-amber-700 block">Stale / Discrepancy</span>
                <span className="text-lg font-bold text-amber-900">
                  {statusData.stats.stale + statusData.stats.conflicting_sources} Issues
                </span>
              </div>
            </div>
          )}

          {/* Configured Sources List */}
          <div>
            <div className="flex items-center justify-between mb-3">
              <h4 className="text-xs font-bold text-slate-800 uppercase tracking-wider">
                Configured Legitimate Official Bank Portals
              </h4>
              <button
                onClick={handleTriggerIngestion}
                disabled={ingesting}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-sky-600 text-white hover:bg-sky-500 disabled:bg-slate-300"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${ingesting ? 'animate-spin' : ''}`} />
                <span>{ingesting ? 'Ingesting Sources...' : 'Trigger Re-Ingestion'}</span>
              </button>
            </div>

            <div className="divide-y divide-slate-100 border border-slate-200 rounded-xl overflow-hidden bg-white">
              {sources.map((src, idx) => (
                <div key={idx} className="p-3.5 flex flex-wrap items-center justify-between gap-3 text-xs">
                  <div>
                    <div className="flex items-center gap-2 mb-0.5">
                      <span className="font-bold text-slate-900">{src.product_name}</span>
                      <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-slate-100 text-slate-600 border border-slate-200 uppercase">
                        {src.product_type}
                      </span>
                    </div>
                    <div className="text-[11px] text-slate-500 flex items-center gap-2">
                      <span className="font-semibold text-slate-700">{src.institution}</span>
                      <span>•</span>
                      <span className="font-mono text-slate-400">{src.domain}</span>
                    </div>
                  </div>

                  <div className="flex items-center gap-3">
                    <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md text-[11px] font-semibold text-emerald-700 bg-emerald-50 border border-emerald-200">
                      <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
                      Whitelisted & Safe
                    </span>
                    <a
                      href={src.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-slate-400 hover:text-slate-700"
                    >
                      <ExternalLink className="w-4 h-4" />
                    </a>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="p-4 bg-slate-50 border-t border-slate-100 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 text-xs font-semibold bg-slate-900 text-white rounded-lg hover:bg-slate-800"
          >
            Close Dashboard
          </button>
        </div>
      </div>
    </div>
  );
};
