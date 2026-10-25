import React from 'react';
import { X, ShieldCheck, ExternalLink, Calendar, CheckCircle2, AlertCircle } from 'lucide-react';
import { Product } from '../types';

interface EvidenceModalProps {
  product: Product | null;
  isOpen: boolean;
  onClose: () => void;
}

export const EvidenceModal: React.FC<EvidenceModalProps> = ({
  product,
  isOpen,
  onClose,
}) => {
  if (!isOpen || !product) return null;

  const evidences = product.field_evidences || [];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-sm animate-fadeIn">
      <div className="bg-white rounded-2xl shadow-xl border border-slate-200 w-full max-w-2xl max-h-[85vh] flex flex-col overflow-hidden">
        {/* Header */}
        <div className="p-5 border-b border-slate-100 flex items-start justify-between gap-3">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="text-xs font-bold text-sky-700 bg-sky-50 px-2 py-0.5 rounded-md border border-sky-200">
                {product.issuer}
              </span>
              <span className="text-xs text-slate-500">•</span>
              <span className="text-xs text-slate-500 capitalize">{product.product_type.replace('_', ' ')}</span>
            </div>
            <h3 className="text-base font-bold text-slate-900">
              Verified Evidence & Sources: {product.product_name}
            </h3>
            <p className="text-xs text-slate-500 mt-0.5">
              Every financial attribute below was extracted directly from official bank portals and validated.
            </p>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-100"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Evidence List */}
        <div className="p-5 overflow-y-auto space-y-4">
          <div className="p-3 bg-slate-50 rounded-xl border border-slate-200/80 flex items-center justify-between text-xs">
            <div className="flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-emerald-600" />
              <span className="font-semibold text-slate-800">
                Overall Quality Status:
              </span>
              <span className="font-bold text-emerald-700 uppercase tracking-wide">
                {product.data_quality_status}
              </span>
            </div>
            <a
              href={product.canonical_url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-sky-600 hover:text-sky-700 inline-flex items-center gap-1 font-semibold"
            >
              <span>Visit Official Page</span>
              <ExternalLink className="w-3 h-3" />
            </a>
          </div>

          <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider">
            Field-Level Citations ({evidences.length})
          </h4>

          {evidences.length === 0 ? (
            <p className="text-xs text-slate-500 italic">
              No individual field excerpts recorded yet. Product verified against canonical portal.
            </p>
          ) : (
            evidences.map((ev, idx) => (
              <div
                key={idx}
                className="p-3.5 rounded-xl border border-slate-200 bg-white shadow-xs space-y-2"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-bold text-slate-800 font-mono">
                      {ev.field_name}
                    </span>
                    <span className="text-[11px] font-semibold text-emerald-700 bg-emerald-50 border border-emerald-200 px-2 py-0.5 rounded-full">
                      {ev.verification_status}
                    </span>
                  </div>
                  <span className="text-[10px] text-slate-400">
                    Confidence: {Math.round(ev.confidence * 100)}%
                  </span>
                </div>

                <div className="text-xs">
                  <span className="text-slate-500 font-medium">Normalized Value: </span>
                  <span className="font-bold text-slate-900">
                    {typeof ev.normalized_value === 'object'
                      ? JSON.stringify(ev.normalized_value)
                      : String(ev.normalized_value)}
                  </span>
                </div>

                <div className="p-2.5 rounded-lg bg-slate-50 border border-slate-100 text-xs text-slate-700 italic font-serif leading-relaxed">
                  "{ev.evidence_excerpt}"
                </div>

                <div className="flex items-center justify-between text-[11px] text-slate-400 pt-1">
                  <span className="truncate max-w-xs">{ev.source_url}</span>
                  <span className="flex items-center gap-1">
                    <Calendar className="w-3 h-3" />
                    <span>{new Date(ev.verified_at).toLocaleDateString()}</span>
                  </span>
                </div>
              </div>
            ))
          )}
        </div>

        {/* Footer */}
        <div className="p-4 bg-slate-50 border-t border-slate-100 flex items-center justify-between">
          <p className="text-[11px] text-slate-500">
            Terms are subject to periodic bank updates and applicant underwriting.
          </p>
          <button
            onClick={onClose}
            className="px-4 py-1.5 text-xs font-semibold bg-slate-900 text-white rounded-lg hover:bg-slate-800"
          >
            Close Inspector
          </button>
        </div>
      </div>
    </div>
  );
};
