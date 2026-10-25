import React, { useState } from 'react';
import { Send, Sparkles, CreditCard, Landmark, ArrowRight } from 'lucide-react';

interface NaturalLanguageProfileInputProps {
  onSubmit: (message: string, category: string) => void;
  isLoading: boolean;
  selectedCategory: string;
}

const SAMPLE_PROMPTS = [
  {
    category: 'credit_card',
    title: 'Bangalore Tech Professional',
    text: "I'm 24, working in Bengaluru and earning around ₹65,000 per month. My salary comes into an HDFC account. I spend about ₹8,000 on food and groceries, ₹5,000 on online shopping, and ₹4,000 on travel every month. I want a credit card with good cashback, no joining fee if possible, and preferably a low annual fee. My credit score is approximately 760. I don't want to pay interest or carry a balance.",
  },
  {
    category: 'personal_loan',
    title: 'Personal Loan for Renovation',
    text: "I need a personal loan of ₹3 lakh for 24 months. I earn ₹55,000 monthly, work at a private company, have an existing EMI of ₹7,000, and want to minimize the total interest paid. I prefer lenders with transparent charges and no hidden fees.",
  },
];

export const NaturalLanguageProfileInput: React.FC<NaturalLanguageProfileInputProps> = ({
  onSubmit,
  isLoading,
  selectedCategory,
}) => {
  const [input, setInput] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;
    onSubmit(input.trim(), selectedCategory);
  };

  const handleUsePrompt = (text: string, cat: string) => {
    setInput(text);
    onSubmit(text, cat);
  };

  return (
    <div className="w-full max-w-4xl mx-auto">
      <div className="bg-white rounded-2xl shadow-sm border border-slate-200/90 p-5 md:p-7">
        <div className="flex items-center gap-2 mb-3">
          <div className="p-1.5 rounded-lg bg-sky-50 text-sky-600">
            <Sparkles className="w-4 h-4" />
          </div>
          <h2 className="text-base font-semibold text-slate-900">
            Describe yourself in simple words
          </h2>
          <span className="text-xs text-slate-500 hidden sm:inline ml-auto">
            No 50-field forms • LLM structured • Deterministic ranking
          </span>
        </div>

        <form onSubmit={handleSubmit} className="relative">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={isLoading}
            rows={4}
            placeholder="Tell us about your monthly income, employer, typical expenses (groceries, shopping, travel), or desired loan amount & tenure..."
            className="w-full p-4 text-sm text-slate-800 bg-slate-50/70 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-sky-500/20 focus:border-sky-500 transition-all resize-none placeholder:text-slate-400"
          />

          <div className="flex flex-wrap items-center justify-between gap-3 mt-3 pt-3 border-t border-slate-100">
            <div className="text-xs text-slate-500 flex items-center gap-2">
              <span className="font-medium text-slate-700">Tip:</span>
              <span>Mention your income, city, CIBIL score, and spending goals.</span>
            </div>

            <button
              type="submit"
              disabled={!input.trim() || isLoading}
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-slate-900 hover:bg-slate-800 disabled:bg-slate-300 text-white text-xs font-semibold shadow-sm transition-all"
            >
              {isLoading ? (
                <>
                  <div className="w-3.5 h-3.5 border-2 border-white/40 border-t-white rounded-full animate-spin" />
                  <span>Structuring Profile...</span>
                </>
              ) : (
                <>
                  <span>Find My Best Options</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </>
              )}
            </button>
          </div>
        </form>

        {/* Quick Example Prompts */}
        <div className="mt-5 pt-4 border-t border-slate-100">
          <p className="text-xs font-medium text-slate-500 mb-2.5">
            Or try an illustrative profile:
          </p>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-2.5">
            {SAMPLE_PROMPTS.map((sp, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => handleUsePrompt(sp.text, sp.category)}
                disabled={isLoading}
                className="text-left p-3 rounded-xl border border-slate-200/80 bg-slate-50/50 hover:bg-sky-50/50 hover:border-sky-200 transition-all group"
              >
                <div className="flex items-center gap-2 mb-1">
                  {sp.category === 'credit_card' ? (
                    <CreditCard className="w-3.5 h-3.5 text-sky-600" />
                  ) : (
                    <Landmark className="w-3.5 h-3.5 text-indigo-600" />
                  )}
                  <span className="text-xs font-semibold text-slate-800 group-hover:text-sky-700">
                    {sp.title}
                  </span>
                </div>
                <p className="text-[11px] text-slate-500 line-clamp-2 leading-relaxed">
                  "{sp.text}"
                </p>
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
