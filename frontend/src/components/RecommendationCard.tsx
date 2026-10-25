import React from 'react';
import {
  ShieldCheck,
  ExternalLink,
  ChevronRight,
  AlertTriangle,
  FileText,
  CheckCircle2,
  AlertCircle,
  HelpCircle,
  Sparkles,
  TrendingUp,
  Percent,
} from 'lucide-react';
import { RecommendationItem } from '../types';

interface RecommendationCardProps {
  item: RecommendationItem;
  onInspectEvidence: (productId: string) => void;
  isCompared: boolean;
  onToggleCompare: (productId: string) => void;
}

export const RecommendationCard: React.FC<RecommendationCardProps> = ({
  item,
  onInspectEvidence,
  isCompared,
  onToggleCompare,
}) => {
  const p = item.product;
  const isCard = p.product_type === 'credit_card';
  const fin = item.financial_calculations;
  const score = Math.round(item.match_score);

  // Score color badge
  const getScoreBadgeColor = (val: number) => {
    if (val >= 85) return 'bg-emerald-500 text-white';
    if (val >= 70) return 'bg-sky-500 text-white';
    if (val >= 50) return 'bg-amber-500 text-white';
    return 'bg-slate-500 text-white';
  };

  // Eligibility Pill
  const getEligibilityBadge = (status: string) => {
    switch (status) {
      case 'meets_published_criteria':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
            <CheckCircle2 className="w-3 h-3 text-emerald-600" />
            Meets Published Criteria
          </span>
        );
      case 'may_meet_criteria':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-amber-50 text-amber-700 border border-amber-200">
            <HelpCircle className="w-3 h-3 text-amber-600" />
            May Meet Criteria
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-rose-50 text-rose-700 border border-rose-200">
            <AlertCircle className="w-3 h-3 text-rose-600" />
            Does Not Meet Published Criteria
          </span>
        );
    }
  };

  return (
    <div className="bg-white rounded-2xl border border-slate-200 shadow-sm hover:shadow-md transition-all overflow-hidden flex flex-col justify-between group">
      <div>
        {/* Card Header */}
        <div className="p-5 pb-4 border-b border-slate-100 flex items-start justify-between gap-3">
          <div>
            <div className="flex items-center gap-2 mb-1.5">
              <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">
                {p.issuer}
              </span>
              <span className="w-1 h-1 rounded-full bg-slate-300" />
              <span className="text-[11px] font-medium text-slate-500 capitalize">
                {p.product_type.replace('_', ' ')}
              </span>
            </div>
            <h3 className="text-base font-bold text-slate-900 group-hover:text-sky-600 transition-colors">
              {p.product_name}
            </h3>
            <div className="mt-2 flex flex-wrap items-center gap-2">
              {getEligibilityBadge(item.eligibility_status)}
              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[10px] font-medium bg-slate-100 text-slate-600 border border-slate-200">
                <ShieldCheck className="w-3 h-3 text-emerald-600" />
                {p.data_quality_status}
              </span>
            </div>
          </div>

          {/* Match Score Badge */}
          <div className="flex flex-col items-center">
            <div
              className={`w-12 h-12 rounded-xl flex flex-col items-center justify-center font-black shadow-sm ${getScoreBadgeColor(
                score
              )}`}
            >
              <span className="text-base leading-none">{score}</span>
              <span className="text-[9px] font-medium opacity-80 uppercase tracking-tighter">Score</span>
            </div>
          </div>
        </div>

        {/* Verified Financial Highlights */}
        <div className="p-5 bg-slate-50/70 border-b border-slate-100 grid grid-cols-2 sm:grid-cols-3 gap-3 text-xs">
          {isCard ? (
            <>
              <div>
                <span className="text-slate-500 block text-[11px]">Annual Fee</span>
                <span className="font-bold text-slate-900">
                  {p.structured_terms.annual_fee === 0
                    ? 'Lifetime Free (₹0)'
                    : `₹${p.structured_terms.annual_fee?.toLocaleString('en-IN')}`}
                </span>
                {fin.fee_waived && (
                  <span className="text-[10px] text-emerald-600 block font-semibold">
                    Fee Waived on Spend
                  </span>
                )}
              </div>

              <div>
                <span className="text-slate-500 block text-[11px]">Top Cashback</span>
                <span className="font-bold text-slate-900">
                  {p.structured_terms.online_shopping_cashback_pct || p.structured_terms.grocery_cashback_pct || p.structured_terms.base_cashback_pct || 1}%
                </span>
                <span className="text-[10px] text-slate-500 block">Accelerated Partner Rate</span>
              </div>

              <div className="col-span-2 sm:col-span-1">
                <span className="text-slate-500 block text-[11px]">Est. Net Annual Benefit</span>
                <span className="font-bold text-emerald-700 text-sm">
                  +₹{(fin.net_annual_benefit || 0).toLocaleString('en-IN')}
                </span>
                <span className="text-[10px] text-slate-500 block">After fee deduction</span>
              </div>
            </>
          ) : (
            <>
              <div>
                <span className="text-slate-500 block text-[11px]">Est. Monthly EMI</span>
                <span className="font-bold text-slate-900">
                  ₹{Math.round(fin.estimated_emi_min || 0).toLocaleString('en-IN')} - ₹{Math.round(fin.estimated_emi_max || 0).toLocaleString('en-IN')}
                </span>
                <span className="text-[10px] text-slate-500 block">Based on rate range</span>
              </div>

              <div>
                <span className="text-slate-500 block text-[11px]">Advertised Interest</span>
                <span className="font-bold text-slate-900">
                  {p.structured_terms.interest_rate_min}% - {p.structured_terms.interest_rate_max}% p.a.
                </span>
                <span className="text-[10px] text-slate-500 block">Nominal reducing rate</span>
              </div>

              <div className="col-span-2 sm:col-span-1">
                <span className="text-slate-500 block text-[11px]">Processing Charge</span>
                <span className="font-bold text-slate-900">
                  ₹{Math.round(fin.estimated_processing_fee || 0).toLocaleString('en-IN')}
                </span>
                <span className="text-[10px] text-slate-500 block">Includes 18% GST</span>
              </div>
            </>
          )}
        </div>

        {/* Personalized Reasoning */}
        <div className="p-5 space-y-3">
          <div>
            <div className="flex items-center gap-1.5 text-xs font-semibold text-slate-800 mb-1">
              <Sparkles className="w-3.5 h-3.5 text-sky-600" />
              <span>Why This Matches You:</span>
            </div>
            <p className="text-xs text-slate-600 leading-relaxed">
              {item.explanation.why_it_matches}
            </p>
          </div>

          {/* Trade-offs & Drawbacks */}
          {item.explanation.drawbacks_and_tradeoffs && item.explanation.drawbacks_and_tradeoffs.length > 0 && (
            <div className="p-3 rounded-xl bg-amber-50/70 border border-amber-200/80 text-xs">
              <div className="flex items-center gap-1.5 font-semibold text-amber-900 mb-1">
                <AlertTriangle className="w-3.5 h-3.5 text-amber-600" />
                <span>Trade-offs & Exclusions:</span>
              </div>
              <ul className="list-disc list-inside space-y-0.5 text-amber-800 text-[11px]">
                {item.explanation.drawbacks_and_tradeoffs.slice(0, 2).map((drawback, dIdx) => (
                  <li key={dIdx}>{drawback}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </div>

      {/* Card Footer Actions */}
      <div className="p-4 bg-slate-50 border-t border-slate-100 flex items-center justify-between gap-2">
        <label className="flex items-center gap-2 cursor-pointer select-none text-xs text-slate-700 font-medium">
          <input
            type="checkbox"
            checked={isCompared}
            onChange={() => onToggleCompare(p.id)}
            className="w-4 h-4 rounded text-sky-600 border-slate-300 focus:ring-sky-500"
          />
          <span>Compare</span>
        </label>

        <div className="flex items-center gap-2">
          <button
            onClick={() => onInspectEvidence(p.id)}
            className="inline-flex items-center gap-1 px-3 py-1.5 text-xs font-medium text-slate-700 bg-white hover:bg-slate-100 border border-slate-200 rounded-lg transition-colors"
            title="Inspect scraped text excerpts and proof"
          >
            <FileText className="w-3.5 h-3.5 text-slate-500" />
            <span>Evidence</span>
          </button>

          <a
            href={p.canonical_url}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1 px-3 py-1.5 text-xs font-semibold text-white bg-slate-900 hover:bg-slate-800 rounded-lg transition-colors shadow-sm"
          >
            <span>Official Portal</span>
            <ExternalLink className="w-3 h-3" />
          </a>
        </div>
      </div>
    </div>
  );
};
