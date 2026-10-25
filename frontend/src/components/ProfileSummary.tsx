import React, { useState } from 'react';
import {
  User,
  IndianRupee,
  Briefcase,
  Gauge,
  MapPin,
  Edit2,
  Sparkles,
  ShoppingBag,
  Utensils,
  Plane,
  CheckCircle2,
} from 'lucide-react';
import { FinancialProfile } from '../types';

interface ProfileSummaryProps {
  profile: FinancialProfile;
  profileId: string;
  onUpdate: (updates: Record<string, any>) => void;
  onGenerateRecs: () => void;
  isLoadingRecs: boolean;
  onOpenClarifications?: () => void;
  hasClarifications: boolean;
}

export const ProfileSummary: React.FC<ProfileSummaryProps> = ({
  profile,
  onUpdate,
  onGenerateRecs,
  isLoadingRecs,
  onOpenClarifications,
  hasClarifications,
}) => {
  const [isEditing, setIsEditing] = useState(false);
  const [income, setIncome] = useState(profile.monthly_income?.value || 60000);
  const [creditScore, setCreditScore] = useState(profile.credit_score?.value || 750);
  const [empType, setEmpType] = useState(profile.employment_type?.value || 'salaried');
  const [city, setCity] = useState(profile.city?.value || 'Bengaluru');
  const [loanAmount, setLoanAmount] = useState(profile.loan_preferences?.requested_amount || 0);
  const [loanTenure, setLoanTenure] = useState(profile.loan_preferences?.requested_tenure_months || 0);

  const isLoan = profile.preferred_product === 'personal_loan' || (profile.preferred_product === 'both' && Boolean(profile.loan_preferences?.requested_amount));
  const isCard = profile.preferred_product === 'credit_card' || profile.preferred_product === 'both';

  const handleSave = () => {
    const payload: Record<string, any> = {
      monthly_income: Number(income),
      credit_score: Number(creditScore),
      employment_type: empType,
      city: city,
    };
    if (isLoan && loanAmount > 0) {
      payload.loan_preferences = {
        requested_amount: Number(loanAmount),
        requested_tenure_months: Number(loanTenure),
      };
    }
    onUpdate(payload);
    setIsEditing(false);
  };

  return (
    <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-5 md:p-6 mb-8">
      <div className="flex flex-wrap items-center justify-between gap-3 pb-4 border-b border-slate-100">
        <div className="flex items-center gap-2">
          <div className="p-1.5 rounded-lg bg-emerald-50 text-emerald-600">
            <CheckCircle2 className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-slate-900">Your Inferred Financial Profile</h3>
            <p className="text-xs text-slate-500">
              Structured automatically from your conversation. You can edit any field.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {hasClarifications && onOpenClarifications && (
            <button
              onClick={onOpenClarifications}
              className="px-3 py-1.5 text-xs font-semibold text-amber-800 bg-amber-50 hover:bg-amber-100 border border-amber-200 rounded-lg transition-colors animate-pulse"
            >
              Answer 1-2 Quick Questions
            </button>
          )}

          <button
            onClick={() => setIsEditing(!isEditing)}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-slate-700 bg-slate-100 hover:bg-slate-200 rounded-lg transition-colors border border-slate-200"
          >
            <Edit2 className="w-3.5 h-3.5" />
            <span>{isEditing ? 'Cancel Edit' : 'Edit Fields'}</span>
          </button>

          <button
            onClick={onGenerateRecs}
            disabled={isLoadingRecs}
            className="inline-flex items-center gap-1.5 px-4 py-1.5 text-xs font-semibold text-white bg-sky-600 hover:bg-sky-500 disabled:bg-slate-300 rounded-lg shadow-sm transition-all"
          >
            {isLoadingRecs ? (
              <>
                <div className="w-3 h-3 border-2 border-white/40 border-t-white rounded-full animate-spin" />
                <span>Evaluating...</span>
              </>
            ) : (
              <>
                <Sparkles className="w-3.5 h-3.5" />
                <span>Run Recommendations</span>
              </>
            )}
          </button>
        </div>
      </div>

      {isEditing ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4 pt-4">
          <div>
            <label className="block text-xs font-medium text-slate-600 mb-1">Monthly Income (₹)</label>
            <input
              type="number"
              value={income}
              onChange={(e) => setIncome(Number(e.target.value))}
              className="w-full text-xs p-2.5 border border-slate-300 rounded-lg"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-600 mb-1">Credit Score</label>
            <input
              type="number"
              value={creditScore}
              onChange={(e) => setCreditScore(Number(e.target.value))}
              className="w-full text-xs p-2.5 border border-slate-300 rounded-lg"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-600 mb-1">Employment</label>
            <select
              value={empType}
              onChange={(e) => setEmpType(e.target.value)}
              className="w-full text-xs p-2.5 border border-slate-300 rounded-lg bg-white"
            >
              <option value="salaried">Salaried</option>
              <option value="self_employed">Self Employed</option>
              <option value="business">Business Owner</option>
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-600 mb-1">City</label>
            <input
              type="text"
              value={city}
              onChange={(e) => setCity(e.target.value)}
              className="w-full text-xs p-2.5 border border-slate-300 rounded-lg"
            />
          </div>
          {isLoan && (
            <>
              <div>
                <label className="block text-xs font-medium text-slate-600 mb-1">Desired Loan Amount (₹)</label>
                <input
                  type="number"
                  value={loanAmount}
                  onChange={(e) => setLoanAmount(Number(e.target.value))}
                  className="w-full text-xs p-2.5 border border-slate-300 rounded-lg"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-slate-600 mb-1">Desired Tenure (Months)</label>
                <input
                  type="number"
                  value={loanTenure}
                  onChange={(e) => setLoanTenure(Number(e.target.value))}
                  className="w-full text-xs p-2.5 border border-slate-300 rounded-lg"
                />
              </div>
            </>
          )}
          <div className="sm:col-span-2 md:col-span-4 flex justify-end gap-2 pt-2">
            <button
              onClick={handleSave}
              className="px-4 py-2 text-xs font-semibold bg-slate-900 text-white rounded-lg hover:bg-slate-800"
            >
              Save Profile Updates
            </button>
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-3 pt-4">
          {/* Income */}
          <div className="p-3 rounded-xl bg-slate-50 border border-slate-100">
            <div className="flex items-center gap-1.5 text-slate-500 mb-1">
              <IndianRupee className="w-3.5 h-3.5" />
              <span className="text-[11px] font-medium uppercase tracking-wider">Income</span>
            </div>
            <div className="text-sm font-bold text-slate-900">
              ₹{(profile.monthly_income?.value || 0).toLocaleString('en-IN')}/mo
            </div>
            <span className="text-[10px] text-slate-400">
              {profile.monthly_income?.source || 'user_provided'}
            </span>
          </div>

          {/* Credit Score */}
          <div className="p-3 rounded-xl bg-slate-50 border border-slate-100">
            <div className="flex items-center gap-1.5 text-slate-500 mb-1">
              <Gauge className="w-3.5 h-3.5" />
              <span className="text-[11px] font-medium uppercase tracking-wider">CIBIL Score</span>
            </div>
            <div className="text-sm font-bold text-slate-900">
              {profile.credit_score?.value || 'Unstated'}
            </div>
            <span className="text-[10px] text-emerald-600 font-medium">
              {profile.credit_score?.value ? 'High Tier' : 'Default guidance'}
            </span>
          </div>

          {/* Employment */}
          <div className="p-3 rounded-xl bg-slate-50 border border-slate-100">
            <div className="flex items-center gap-1.5 text-slate-500 mb-1">
              <Briefcase className="w-3.5 h-3.5" />
              <span className="text-[11px] font-medium uppercase tracking-wider">Employment</span>
            </div>
            <div className="text-sm font-bold text-slate-900 capitalize">
              {profile.employment_type?.value || 'Salaried'}
            </div>
            <span className="text-[10px] text-slate-400">
              {profile.card_preferences.existing_bank ? `Banks with ${profile.card_preferences.existing_bank}` : 'Standard'}
            </span>
          </div>

          {/* City */}
          <div className="p-3 rounded-xl bg-slate-50 border border-slate-100">
            <div className="flex items-center gap-1.5 text-slate-500 mb-1">
              <MapPin className="w-3.5 h-3.5" />
              <span className="text-[11px] font-medium uppercase tracking-wider">Location</span>
            </div>
            <div className="text-sm font-bold text-slate-900">
              {profile.city?.value || 'Bengaluru'}
            </div>
            <span className="text-[10px] text-slate-400">Tier 1 Metro</span>
          </div>

          {/* Category-specific card metrics */}
          {isCard && (
            <>
              <div className="p-3 rounded-xl bg-slate-50 border border-slate-100">
                <div className="flex items-center gap-1.5 text-slate-500 mb-1">
                  <ShoppingBag className="w-3.5 h-3.5" />
                  <span className="text-[11px] font-medium uppercase tracking-wider">Top Spends</span>
                </div>
                <div className="text-sm font-bold text-slate-900">
                  ₹{(profile.spending.food_groceries + profile.spending.online_shopping).toLocaleString('en-IN')}
                </div>
                <span className="text-[10px] text-sky-600 font-medium">Grocery + Shopping</span>
              </div>

              <div className="p-3 rounded-xl bg-slate-50 border border-slate-100">
                <div className="flex items-center gap-1.5 text-slate-500 mb-1">
                  <Sparkles className="w-3.5 h-3.5" />
                  <span className="text-[11px] font-medium uppercase tracking-wider">Fee Sensitivity</span>
                </div>
                <div className="text-sm font-bold text-slate-900">
                  {profile.card_preferences.low_annual_fee ? 'Low / Zero Fee' : 'Flexible'}
                </div>
                <span className="text-[10px] text-slate-400">Priority filter</span>
              </div>
            </>
          )}

          {/* Category-specific loan metrics */}
          {isLoan && (
            <>
              <div className="p-3 rounded-xl bg-slate-50 border border-slate-100">
                <div className="flex items-center gap-1.5 text-slate-500 mb-1">
                  <IndianRupee className="w-3.5 h-3.5" />
                  <span className="text-[11px] font-medium uppercase tracking-wider">Loan Need</span>
                </div>
                <div className="text-sm font-bold text-slate-900">
                  ₹{(profile.loan_preferences.requested_amount || 300000).toLocaleString('en-IN')}
                </div>
                <span className="text-[10px] text-indigo-600 font-medium">
                  {profile.loan_preferences.requested_tenure_months || 24} Months
                </span>
              </div>

              <div className="p-3 rounded-xl bg-slate-50 border border-slate-100">
                <div className="flex items-center gap-1.5 text-slate-500 mb-1">
                  <User className="w-3.5 h-3.5" />
                  <span className="text-[11px] font-medium uppercase tracking-wider">Current EMI</span>
                </div>
                <div className="text-sm font-bold text-slate-900">
                  ₹{(profile.existing_monthly_emi?.value || 0).toLocaleString('en-IN')}
                </div>
                <span className="text-[10px] text-slate-400">Existing obligation</span>
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
};
