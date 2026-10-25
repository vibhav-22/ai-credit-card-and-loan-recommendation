import React from 'react';
import { ShieldCheck, Sparkles, RefreshCw, Database } from 'lucide-react';

interface NavbarProps {
  onOpenIngestion: () => void;
  onReset: () => void;
  selectedCategory: string;
  onSelectCategory: (cat: string) => void;
}

export const Navbar: React.FC<NavbarProps> = ({
  onOpenIngestion,
  onReset,
  selectedCategory,
  onSelectCategory,
}) => {
  return (
    <header className="sticky top-0 z-40 w-full border-b border-slate-200 bg-white/90 backdrop-blur-md">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Brand */}
        <div className="flex items-center gap-3 cursor-pointer" onClick={onReset}>
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-sky-600 to-indigo-600 flex items-center justify-center text-white shadow-sm shadow-sky-500/20">
            <Sparkles className="w-5 h-5" />
          </div>
          <div>
            <span className="font-bold text-lg text-slate-900 tracking-tight">FinMatch</span>
            <span className="text-xs ml-1.5 px-2 py-0.5 rounded-full bg-sky-100 text-sky-800 font-semibold uppercase tracking-wider">AI</span>
          </div>
        </div>

        {/* Category Pills */}
        <div className="hidden sm:flex items-center gap-1 p-1 bg-slate-100 rounded-xl border border-slate-200/80">
          <button
            onClick={() => onSelectCategory('both')}
            className={`px-3.5 py-1.5 text-xs font-medium rounded-lg transition-all ${
              selectedCategory === 'both'
                ? 'bg-white text-slate-900 shadow-sm'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            All Products
          </button>
          <button
            onClick={() => onSelectCategory('credit_card')}
            className={`px-3.5 py-1.5 text-xs font-medium rounded-lg transition-all ${
              selectedCategory === 'credit_card'
                ? 'bg-white text-slate-900 shadow-sm'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            Credit Cards
          </button>
          <button
            onClick={() => onSelectCategory('personal_loan')}
            className={`px-3.5 py-1.5 text-xs font-medium rounded-lg transition-all ${
              selectedCategory === 'personal_loan'
                ? 'bg-white text-slate-900 shadow-sm'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            Personal Loans
          </button>
        </div>

        {/* Actions */}
        <div className="flex items-center gap-3">
          <button
            onClick={onOpenIngestion}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-slate-700 bg-slate-100 hover:bg-slate-200 rounded-lg transition-colors border border-slate-200"
            title="Inspect Official Sources & Ingestion Status"
          >
            <Database className="w-3.5 h-3.5 text-sky-600" />
            <span className="hidden md:inline">Bank Sources</span>
          </button>

          <button
            onClick={onReset}
            className="flex items-center gap-1 px-3 py-1.5 text-xs font-medium text-slate-600 hover:text-slate-900 bg-white hover:bg-slate-50 border border-slate-200 rounded-lg transition-colors"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>New Search</span>
          </button>

          <div className="hidden lg:flex items-center gap-1 text-[11px] font-medium text-emerald-700 bg-emerald-50 border border-emerald-200 px-2.5 py-1 rounded-full">
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
            <span>100% Verified Evidence</span>
          </div>
        </div>
      </div>
    </header>
  );
};
