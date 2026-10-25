import React from 'react';
import { X, Check, ExternalLink, ShieldCheck } from 'lucide-react';
import { ComparisonResponse } from '../types';

interface ProductComparisonModalProps {
  comparison: ComparisonResponse | null;
  isOpen: boolean;
  onClose: () => void;
}

export const ProductComparisonModal: React.FC<ProductComparisonModalProps> = ({
  comparison,
  isOpen,
  onClose,
}) => {
  if (!isOpen || !comparison || comparison.products.length === 0) return null;

  const isCard = comparison.category === 'credit_card';

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/50 backdrop-blur-sm animate-fadeIn">
      <div className="bg-white rounded-2xl shadow-2xl border border-slate-200 w-full max-w-5xl max-h-[90vh] flex flex-col overflow-hidden">
        {/* Header */}
        <div className="p-5 border-b border-slate-100 flex items-center justify-between">
          <div>
            <h3 className="text-base font-bold text-slate-900">
              Side-by-Side Financial Product Comparison
            </h3>
            <p className="text-xs text-slate-500">
              Comparing {comparison.products.length} {isCard ? 'credit cards' : 'personal loans'} across verified parameters
            </p>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-100"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content Table */}
        <div className="p-5 overflow-auto">
          <table className="w-full text-xs text-left border-collapse">
            <thead>
              <tr className="border-b border-slate-200">
                <th className="p-3 bg-slate-50 font-bold text-slate-500 uppercase tracking-wider w-44">
                  Parameter
                </th>
                {comparison.products.map((item, idx) => (
                  <th key={idx} className="p-3 bg-slate-50 font-bold text-slate-900 min-w-52">
                    <div className="text-[11px] font-bold text-sky-700 uppercase">{item.product.issuer}</div>
                    <div className="text-sm font-extrabold text-slate-900">{item.product.product_name}</div>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {isCard ? (
                <>
                  <tr>
                    <td className="p-3 font-semibold text-slate-600">Joining Fee</td>
                    {comparison.products.map((item, idx) => (
                      <td key={idx} className="p-3 text-slate-900 font-bold">
                        {item.product.structured_terms.joining_fee === 0
                          ? '₹0 (Free)'
                          : `₹${item.product.structured_terms.joining_fee?.toLocaleString('en-IN')}`}
                      </td>
                    ))}
                  </tr>
                  <tr>
                    <td className="p-3 font-semibold text-slate-600">Annual Renewal Fee</td>
                    {comparison.products.map((item, idx) => (
                      <td key={idx} className="p-3 text-slate-900 font-bold">
                        {item.product.structured_terms.annual_fee === 0
                          ? '₹0 (Lifetime Free)'
                          : `₹${item.product.structured_terms.annual_fee?.toLocaleString('en-IN')}`}
                      </td>
                    ))}
                  </tr>
                  <tr>
                    <td className="p-3 font-semibold text-slate-600">Fee Waiver Spend</td>
                    {comparison.products.map((item, idx) => (
                      <td key={idx} className="p-3 text-slate-700">
                        {item.product.structured_terms.fee_waiver_spend_threshold
                          ? `₹${item.product.structured_terms.fee_waiver_spend_threshold?.toLocaleString('en-IN')}/year`
                          : 'No published waiver'}
                      </td>
                    ))}
                  </tr>
                  <tr>
                    <td className="p-3 font-semibold text-slate-600">Accelerated Cashback</td>
                    {comparison.products.map((item, idx) => (
                      <td key={idx} className="p-3 text-sky-700 font-bold">
                        {item.product.structured_terms.online_shopping_cashback_pct || item.product.structured_terms.grocery_cashback_pct || 1}%
                        <span className="text-[10px] text-slate-500 font-normal block">Partner shopping / groceries</span>
                      </td>
                    ))}
                  </tr>
                  <tr>
                    <td className="p-3 font-semibold text-slate-600">Reward Cap</td>
                    {comparison.products.map((item, idx) => (
                      <td key={idx} className="p-3 text-slate-700">
                        {item.product.structured_terms.monthly_reward_cap
                          ? `₹${item.product.structured_terms.monthly_reward_cap?.toLocaleString('en-IN')}/month`
                          : 'No monthly limit'}
                      </td>
                    ))}
                  </tr>
                  <tr>
                    <td className="p-3 font-semibold text-slate-600">Projected Annual Benefit</td>
                    {comparison.products.map((item, idx) => (
                      <td key={idx} className="p-3 text-emerald-700 font-extrabold text-sm">
                        +₹{Math.round(item.financial_calculations?.net_annual_benefit || 0).toLocaleString('en-IN')}
                      </td>
                    ))}
                  </tr>
                </>
              ) : (
                <>
                  <tr>
                    <td className="p-3 font-semibold text-slate-600">Advertised Interest</td>
                    {comparison.products.map((item, idx) => (
                      <td key={idx} className="p-3 text-slate-900 font-bold">
                        {item.product.structured_terms.interest_rate_min}% - {item.product.structured_terms.interest_rate_max}% p.a.
                      </td>
                    ))}
                  </tr>
                  <tr>
                    <td className="p-3 font-semibold text-slate-600">Monthly EMI Range</td>
                    {comparison.products.map((item, idx) => (
                      <td key={idx} className="p-3 text-slate-900 font-bold">
                        ₹{Math.round(item.financial_calculations?.estimated_emi_min || 0).toLocaleString('en-IN')} - ₹{Math.round(item.financial_calculations?.estimated_emi_max || 0).toLocaleString('en-IN')}
                      </td>
                    ))}
                  </tr>
                  <tr>
                    <td className="p-3 font-semibold text-slate-600">Borrowing Range</td>
                    {comparison.products.map((item, idx) => (
                      <td key={idx} className="p-3 text-slate-700">
                        ₹{item.product.structured_terms.min_amount?.toLocaleString('en-IN')} to ₹{item.product.structured_terms.max_amount?.toLocaleString('en-IN')}
                      </td>
                    ))}
                  </tr>
                  <tr>
                    <td className="p-3 font-semibold text-slate-600">Tenure Options</td>
                    {comparison.products.map((item, idx) => (
                      <td key={idx} className="p-3 text-slate-700">
                        {item.product.structured_terms.min_tenure_months} to {item.product.structured_terms.max_tenure_months} Months
                      </td>
                    ))}
                  </tr>
                  <tr>
                    <td className="p-3 font-semibold text-slate-600">Processing Fee</td>
                    {comparison.products.map((item, idx) => (
                      <td key={idx} className="p-3 text-slate-700">
                        {item.product.structured_terms.processing_fee_pct}% + 18% GST
                      </td>
                    ))}
                  </tr>
                </>
              )}

              {/* Pros & Cons */}
              <tr>
                <td className="p-3 font-semibold text-slate-600">Key Advantages</td>
                {comparison.products.map((item, idx) => (
                  <td key={idx} className="p-3 text-slate-700">
                    <ul className="space-y-1 list-disc list-inside text-emerald-800 text-[11px]">
                      {item.pros.map((p, pIdx) => (
                        <li key={pIdx}>{p}</li>
                      ))}
                    </ul>
                  </td>
                ))}
              </tr>
              <tr>
                <td className="p-3 font-semibold text-slate-600">Considerations</td>
                {comparison.products.map((item, idx) => (
                  <td key={idx} className="p-3 text-slate-700">
                    <ul className="space-y-1 list-disc list-inside text-amber-800 text-[11px]">
                      {item.cons.map((c, cIdx) => (
                        <li key={cIdx}>{c}</li>
                      ))}
                    </ul>
                  </td>
                ))}
              </tr>
              <tr>
                <td className="p-3 font-semibold text-slate-600">Apply Link</td>
                {comparison.products.map((item, idx) => (
                  <td key={idx} className="p-3">
                    <a
                      href={item.product.canonical_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg bg-slate-900 text-white font-semibold text-[11px] hover:bg-slate-800"
                    >
                      <span>Bank Application</span>
                      <ExternalLink className="w-3 h-3" />
                    </a>
                  </td>
                ))}
              </tr>
            </tbody>
          </table>
        </div>

        {/* Footer */}
        <div className="p-4 bg-slate-50 border-t border-slate-100 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 text-xs font-semibold bg-slate-900 text-white rounded-lg hover:bg-slate-800"
          >
            Close Comparison
          </button>
        </div>
      </div>
    </div>
  );
};
