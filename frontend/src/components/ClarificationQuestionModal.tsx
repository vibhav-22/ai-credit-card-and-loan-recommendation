import React, { useState } from 'react';
import { HelpCircle, X, Check, ArrowRight } from 'lucide-react';
import { ClarificationQuestion } from '../types';

interface ClarificationQuestionModalProps {
  questions: ClarificationQuestion[];
  isOpen: boolean;
  onClose: () => void;
  onSubmitAnswers: (answers: Record<string, string>) => void;
}

export const ClarificationQuestionModal: React.FC<ClarificationQuestionModalProps> = ({
  questions,
  isOpen,
  onClose,
  onSubmitAnswers,
}) => {
  const [selectedAnswers, setSelectedAnswers] = useState<Record<string, string>>({});
  const [customText, setCustomText] = useState<Record<string, string>>({});

  if (!isOpen || questions.length === 0) return null;

  const handleSelectOption = (field: string, option: string) => {
    setSelectedAnswers((prev) => ({
      ...prev,
      [field]: option,
    }));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const finalAnswers: Record<string, string> = { ...selectedAnswers };
    for (const [k, v] of Object.entries(customText)) {
      if (v.trim()) {
        finalAnswers[k] = v.trim();
      }
    }
    onSubmitAnswers(finalAnswers);
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-sm animate-fadeIn">
      <div className="bg-white rounded-2xl shadow-xl border border-slate-200 w-full max-w-lg overflow-hidden">
        <div className="p-5 border-b border-slate-100 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="p-1.5 rounded-lg bg-sky-50 text-sky-600">
              <HelpCircle className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-slate-900">Adaptive Clarification</h3>
              <p className="text-xs text-slate-500">
                Answering these 1-2 details improves recommendation accuracy.
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-100"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-5 space-y-5">
          {questions.map((q, idx) => (
            <div key={idx} className="space-y-2">
              <div className="flex items-start justify-between gap-2">
                <label className="text-xs font-semibold text-slate-800">
                  {q.question}
                </label>
                <span className="text-[10px] text-slate-400 font-medium">Optional</span>
              </div>
              <p className="text-[11px] text-slate-500">{q.reason}</p>

              {q.options && q.options.length > 0 && (
                <div className="flex flex-wrap gap-1.5 pt-1">
                  {q.options.map((opt, optIdx) => {
                    const isSelected = selectedAnswers[q.field] === opt;
                    return (
                      <button
                        key={optIdx}
                        type="button"
                        onClick={() => handleSelectOption(q.field, opt)}
                        className={`px-3 py-1.5 text-xs rounded-lg border transition-all flex items-center gap-1.5 ${
                          isSelected
                            ? 'bg-sky-50 border-sky-400 text-sky-800 font-semibold'
                            : 'bg-slate-50 border-slate-200 text-slate-700 hover:bg-slate-100'
                        }`}
                      >
                        {isSelected && <Check className="w-3 h-3 text-sky-600" />}
                        <span>{opt}</span>
                      </button>
                    );
                  })}
                </div>
              )}

              <input
                type="text"
                placeholder="Or type custom details..."
                value={customText[q.field] || ''}
                onChange={(e) =>
                  setCustomText({ ...customText, [q.field]: e.target.value })
                }
                className="w-full text-xs p-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-1 focus:ring-sky-500"
              />
            </div>
          ))}

          <div className="pt-3 border-t border-slate-100 flex items-center justify-between">
            <button
              type="button"
              onClick={onClose}
              className="text-xs font-medium text-slate-500 hover:text-slate-800"
            >
              Skip for now
            </button>

            <button
              type="submit"
              className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-slate-900 text-white text-xs font-semibold hover:bg-slate-800 transition-colors shadow-sm"
            >
              <span>Update & Recalculate</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
