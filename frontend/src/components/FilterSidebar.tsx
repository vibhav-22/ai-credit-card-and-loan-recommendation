import React from 'react';
import { Filter, SlidersHorizontal, Check } from 'lucide-react';

interface FilterSidebarProps {
  selectedCategory: string;
  onSelectCategory: (cat: string) => void;
  selectedIssuer: string;
  onSelectIssuer: (issuer: string) => void;
  zeroFeeOnly: boolean;
  onToggleZeroFee: (val: boolean) => void;
  minScore: number;
  onMinScoreChange: (score: number) => void;
  eligibilityFilter: string;
  onEligibilityFilterChange: (status: string) => void;
  issuers: string[];
}

export const FilterSidebar: React.FC<FilterSidebarProps> = ({
  selectedCategory,
  onSelectCategory,
  selectedIssuer,
  onSelectIssuer,
  zeroFeeOnly,
  onToggleZeroFee,
  minScore,
  onMinScoreChange,
  eligibilityFilter,
  onEligibilityFilterChange,
  issuers,
}) => {
  return (
    <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-xs space-y-6">
      <div className="flex items-center justify-between pb-3 border-b border-slate-100">
        <div className="flex items-center gap-2">
          <SlidersHorizontal className="w-4 h-4 text-slate-700" />
          <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
            Filters
          </h3>
        </div>
      </div>

      {/* Category */}
      <div className="space-y-2">
        <label className="text-xs font-bold text-slate-700 block">Category</label>
        <div className="space-y-1">
          {[
            { id: 'both', label: 'All Products' },
            { id: 'credit_card', label: 'Credit Cards Only' },
            { id: 'personal_loan', label: 'Personal Loans Only' },
          ].map((cat) => (
            <button
              key={cat.id}
              onClick={() => onSelectCategory(cat.id)}
              className={`w-full text-left px-3 py-2 text-xs rounded-lg transition-colors flex items-center justify-between ${
                selectedCategory === cat.id
                  ? 'bg-sky-50 text-sky-900 font-bold border border-sky-200'
                  : 'text-slate-600 hover:bg-slate-50'
              }`}
            >
              <span>{cat.label}</span>
              {selectedCategory === cat.id && <Check className="w-3.5 h-3.5 text-sky-600" />}
            </button>
          ))}
        </div>
      </div>

      {/* Bank / Issuer */}
      <div className="space-y-2">
        <label className="text-xs font-bold text-slate-700 block">Institution / Bank</label>
        <select
          value={selectedIssuer}
          onChange={(e) => onSelectIssuer(e.target.value)}
          className="w-full text-xs p-2.5 border border-slate-200 rounded-lg bg-white focus:outline-none focus:ring-1 focus:ring-sky-500"
        >
          <option value="">All Institutions</option>
          {issuers.map((iss, idx) => (
            <option key={idx} value={iss}>
              {iss}
            </option>
          ))}
        </select>
      </div>

      {/* Zero/Low Fee Only toggle */}
      <div className="pt-2">
        <label className="flex items-center gap-2.5 text-xs text-slate-800 font-medium cursor-pointer">
          <input
            type="checkbox"
            checked={zeroFeeOnly}
            onChange={(e) => onToggleZeroFee(e.target.checked)}
            className="w-4 h-4 rounded text-sky-600 border-slate-300 focus:ring-sky-500"
          />
          <span>Zero / Low Annual Fee Only</span>
        </label>
      </div>

      {/* Minimum Match Score Slider */}
      <div className="space-y-2 pt-2 border-t border-slate-100">
        <div className="flex justify-between items-center text-xs">
          <span className="font-bold text-slate-700">Min Match Score</span>
          <span className="font-extrabold text-sky-700">{minScore}/100</span>
        </div>
        <input
          type="range"
          min="0"
          max="95"
          step="5"
          value={minScore}
          onChange={(e) => onMinScoreChange(Number(e.target.value))}
          className="w-full accent-sky-600 h-1.5 bg-slate-200 rounded-lg cursor-pointer"
        />
      </div>

      {/* Eligibility status filter */}
      <div className="space-y-2 pt-2 border-t border-slate-100">
        <label className="text-xs font-bold text-slate-700 block">Eligibility Status</label>
        <select
          value={eligibilityFilter}
          onChange={(e) => onEligibilityFilterChange(e.target.value)}
          className="w-full text-xs p-2.5 border border-slate-200 rounded-lg bg-white focus:outline-none focus:ring-1 focus:ring-sky-500"
        >
          <option value="">All Eligibility States</option>
          <option value="meets_published_criteria">Meets Published Criteria Only</option>
          <option value="may_meet_criteria">May Meet Criteria</option>
        </select>
      </div>
    </div>
  );
};
