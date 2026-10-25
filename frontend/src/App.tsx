import React, { useState, useEffect } from 'react';
import {
  Sparkles,
  ShieldCheck,
  Layers,
  ArrowRight,
  Filter,
  CheckCircle2,
  AlertCircle,
  TrendingUp,
  Info,
} from 'lucide-react';
import { Navbar } from './components/Navbar';
import { NaturalLanguageProfileInput } from './components/NaturalLanguageProfileInput';
import { ProfileSummary } from './components/ProfileSummary';
import { ClarificationQuestionModal } from './components/ClarificationQuestionModal';
import { RecommendationCard } from './components/RecommendationCard';
import { EvidenceModal } from './components/EvidenceModal';
import { ProductComparisonModal } from './components/ProductComparisonModal';
import { FilterSidebar } from './components/FilterSidebar';
import { IngestionStatusModal } from './components/IngestionStatusModal';
import {
  FinancialProfile,
  RecommendationItem,
  ClarificationQuestion,
  Product,
  ComparisonResponse,
} from './types';
import { api } from './services/api';

export const App: React.FC = () => {
  // Application State
  const [profile, setProfile] = useState<FinancialProfile | null>(null);
  const [profileId, setProfileId] = useState<string | null>(null);
  const [clarifications, setClarifications] = useState<ClarificationQuestion[]>([]);
  const [recommendations, setRecommendations] = useState<RecommendationItem[]>([]);
  
  // Modals & UI controls
  const [isParsing, setIsParsing] = useState(false);
  const [isLoadingRecs, setIsLoadingRecs] = useState(false);
  const [showClarifications, setShowClarifications] = useState(false);
  const [showIngestion, setShowIngestion] = useState(false);
  const [evidenceProduct, setEvidenceProduct] = useState<Product | null>(null);
  const [comparisonData, setComparisonData] = useState<ComparisonResponse | null>(null);
  const [showComparison, setShowComparison] = useState(false);
  const [selectedForCompare, setSelectedForCompare] = useState<string[]>([]);

  // Filters
  const [selectedCategory, setSelectedCategory] = useState<string>('both');
  const [selectedIssuer, setSelectedIssuer] = useState<string>('');
  const [zeroFeeOnly, setZeroFeeOnly] = useState<boolean>(false);
  const [minScore, setMinScore] = useState<number>(0);
  const [eligibilityFilter, setEligibilityFilter] = useState<string>('');

  // Handle parsing initial natural language message
  const handleParseProfile = async (message: string, category: string) => {
    setIsParsing(true);
    try {
      const catParam = category === 'both' ? undefined : category;
      const resp = await api.parseProfile(message, catParam);
      setProfile(resp.profile);
      setProfileId(resp.id);
      setClarifications(resp.clarifications || []);
      
      const targetCat = resp.profile.preferred_product || 'credit_card';
      setSelectedCategory(targetCat);

      // Auto-trigger recommendations
      await runRecommendations(resp.id, targetCat);
      
      if (resp.clarifications && resp.clarifications.length > 0) {
        setShowClarifications(true);
      }
    } catch (err) {
      alert(`Error structuring profile: ${err}`);
    } finally {
      setIsParsing(false);
    }
  };

  // Run recommendation pipeline
  const runRecommendations = async (pId: string, category?: string) => {
    setIsLoadingRecs(true);
    try {
      const targetCat = category || profile?.preferred_product || selectedCategory;
      const resp = await api.generateRecommendations(pId, targetCat);
      setRecommendations(resp.recommendations || []);
    } catch (err) {
      console.error('Error generating recommendations:', err);
    } finally {
      setIsLoadingRecs(false);
    }
  };

  // Profile update
  const handleUpdateProfile = async (updates: Record<string, any>) => {
    if (!profileId) return;
    try {
      const resp = await api.updateProfile(profileId, updates);
      setProfile(resp.profile);
      setClarifications(resp.clarifications || []);
      await runRecommendations(profileId, resp.profile.preferred_product);
    } catch (err) {
      alert(`Update failed: ${err}`);
    }
  };

  // Answering clarification questions
  const handleAnswerClarifications = async (answers: Record<string, string>) => {
    if (!profileId) return;
    const answerMessage = Object.entries(answers)
      .map(([k, v]) => `${k}: ${v}`)
      .join(', ');
    if (!answerMessage.trim()) return;

    try {
      const resp = await api.chatProfile(profileId, answerMessage);
      setProfile(resp.profile);
      setClarifications(resp.clarifications || []);
      await runRecommendations(profileId, resp.profile.preferred_product);
    } catch (err) {
      alert(`Clarification update failed: ${err}`);
    }
  };

  // Inspect Evidence
  const handleInspectEvidence = async (productId: string) => {
    try {
      const fullProd = await api.getProductDetails(productId);
      setEvidenceProduct(fullProd);
    } catch (err) {
      alert(`Could not load evidence: ${err}`);
    }
  };

  // Comparison toggle
  const handleToggleCompare = (productId: string) => {
    setSelectedForCompare((prev) => {
      if (prev.includes(productId)) {
        return prev.filter((id) => id !== productId);
      } else {
        if (prev.length >= 4) {
          alert('You can compare at most 4 products simultaneously.');
          return prev;
        }
        return [...prev, productId];
      }
    });
  };

  // Launch comparison modal
  const handleLaunchComparison = async () => {
    if (selectedForCompare.length < 2) return;
    try {
      const comp = await api.compareProducts(selectedForCompare, profileId || undefined);
      setComparisonData(comp);
      setShowComparison(true);
    } catch (err) {
      alert(`Comparison error: ${err}`);
    }
  };

  // Reset
  const handleReset = () => {
    setProfile(null);
    setProfileId(null);
    setClarifications([]);
    setRecommendations([]);
    setSelectedForCompare([]);
  };

  // Unique issuers from recommendations
  const issuers = Array.from(new Set(recommendations.map((r) => r.product.issuer)));

  // Filter recommendations
  const filteredRecs = recommendations.filter((r) => {
    if (selectedCategory !== 'both' && r.product.product_type !== selectedCategory) {
      return false;
    }
    if (selectedIssuer && r.product.issuer !== selectedIssuer) {
      return false;
    }
    if (zeroFeeOnly) {
      const isFreeCard = r.product.product_type === 'credit_card' && r.product.structured_terms.annual_fee === 0;
      const isLowFeeLoan = r.product.product_type === 'personal_loan' && r.product.structured_terms.processing_fee_pct <= 1.5;
      if (!isFreeCard && !isLowFeeLoan) return false;
    }
    if (r.match_score < minScore) {
      return false;
    }
    if (eligibilityFilter && r.eligibility_status !== eligibilityFilter) {
      return false;
    }
    return true;
  });

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col font-sans">
      <Navbar
        onOpenIngestion={() => setShowIngestion(true)}
        onReset={handleReset}
        selectedCategory={selectedCategory}
        onSelectCategory={setSelectedCategory}
      />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Landing Hero (when no profile yet) */}
        {!profile && (
          <div className="text-center max-w-3xl mx-auto mb-10 pt-4">
            <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-sky-100/80 text-sky-800 border border-sky-200/60 mb-4">
              <Sparkles className="w-3.5 h-3.5 text-sky-600" />
              <span>Next-Gen Financial Intelligence</span>
            </div>
            <h1 className="text-3xl sm:text-4xl md:text-5xl font-black text-slate-900 tracking-tight leading-tight mb-4">
              Find your ideal credit card or loan with natural language.
            </h1>
            <p className="text-sm sm:text-base text-slate-600 max-w-2xl mx-auto leading-relaxed">
              No tedious 40-question questionnaires. Describe your income, spending habits, or loan requirements in plain words. 
              Our AI structures your profile and ranks verified products using deterministic mathematical rules.
            </p>
          </div>
        )}

        {/* Natural Language Input */}
        {!profile && (
          <NaturalLanguageProfileInput
            onSubmit={handleParseProfile}
            isLoading={isParsing}
            selectedCategory={selectedCategory}
          />
        )}

        {/* Profile Summary & Inferred Parameters */}
        {profile && profileId && (
          <ProfileSummary
            profile={profile}
            profileId={profileId}
            onUpdate={handleUpdateProfile}
            onGenerateRecs={() => runRecommendations(profileId)}
            isLoadingRecs={isLoadingRecs}
            hasClarifications={clarifications.length > 0}
            onOpenClarifications={() => setShowClarifications(true)}
          />
        )}

        {/* Recommendation Results & Filters */}
        {profile && (
          <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
            {/* Filter Sidebar */}
            <div className="lg:col-span-1">
              <FilterSidebar
                selectedCategory={selectedCategory}
                onSelectCategory={setSelectedCategory}
                selectedIssuer={selectedIssuer}
                onSelectIssuer={setSelectedIssuer}
                zeroFeeOnly={zeroFeeOnly}
                onToggleZeroFee={setZeroFeeOnly}
                minScore={minScore}
                onMinScoreChange={setMinScore}
                eligibilityFilter={eligibilityFilter}
                onEligibilityFilterChange={setEligibilityFilter}
                issuers={issuers}
              />
            </div>

            {/* Recommendation Cards */}
            <div className="lg:col-span-3 space-y-6">
              <div className="flex items-center justify-between pb-2 border-b border-slate-200">
                <div>
                  <h2 className="text-base font-bold text-slate-900">
                    Personalized Recommendations ({filteredRecs.length})
                  </h2>
                  <p className="text-xs text-slate-500">
                    Ranked deterministically by eligibility compatibility, financial yield, and your priorities.
                  </p>
                </div>
              </div>

              {filteredRecs.length === 0 ? (
                <div className="p-12 text-center bg-white rounded-2xl border border-slate-200">
                  <AlertCircle className="w-8 h-8 text-slate-400 mx-auto mb-2" />
                  <h3 className="text-sm font-bold text-slate-800">No matching products found</h3>
                  <p className="text-xs text-slate-500 mt-1">
                    Try adjusting your filters or lowering the minimum match score threshold.
                  </p>
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                  {filteredRecs.map((rec) => (
                    <RecommendationCard
                      key={rec.id}
                      item={rec}
                      onInspectEvidence={handleInspectEvidence}
                      isCompared={selectedForCompare.includes(rec.product_id)}
                      onToggleCompare={handleToggleCompare}
                    />
                  ))}
                </div>
              )}
            </div>
          </div>
        )}
      </main>

      {/* Floating Compare Action Bar */}
      {selectedForCompare.length >= 2 && (
        <div className="sticky bottom-4 z-30 max-w-md mx-auto w-full px-4">
          <div className="p-3 bg-slate-900 text-white rounded-2xl shadow-xl border border-slate-800 flex items-center justify-between gap-3 animate-slideUp">
            <div className="text-xs">
              <span className="font-bold text-sky-400">{selectedForCompare.length} products</span> selected
            </div>
            <button
              onClick={handleLaunchComparison}
              className="px-4 py-1.5 rounded-xl bg-sky-500 hover:bg-sky-400 text-white text-xs font-bold transition-all shadow-sm"
            >
              Compare Side-by-Side
            </button>
          </div>
        </div>
      )}

      {/* Trust & Transparency Footer */}
      <footer className="mt-16 border-t border-slate-200 bg-white py-8 text-center text-xs text-slate-500">
        <div className="max-w-5xl mx-auto px-4 space-y-2">
          <div className="flex items-center justify-center gap-2 text-slate-700 font-semibold">
            <ShieldCheck className="w-4 h-4 text-emerald-600" />
            <span>FinMatch AI Transparency & Responsible Lending Commitment</span>
          </div>
          <p className="max-w-2xl mx-auto leading-relaxed text-slate-400">
            Recommendations are educational and algorithmic based strictly on verified bank terms and user-provided inputs. 
            FinMatch does not guarantee loan or credit card approval; final terms, interest rates, and issuance remain subject to bank underwriting. 
            We never request, store, or process account passwords, OTPs, or full card numbers.
          </p>
          <div className="text-slate-400 text-[11px] pt-2">
            Targeting the Indian Financial Market (INR ₹, RBI Guidelines, CIBIL Scoring).
          </div>
        </div>
      </footer>

      {/* Modals */}
      <ClarificationQuestionModal
        questions={clarifications}
        isOpen={showClarifications}
        onClose={() => setShowClarifications(false)}
        onSubmitAnswers={handleAnswerClarifications}
      />

      <EvidenceModal
        product={evidenceProduct}
        isOpen={!!evidenceProduct}
        onClose={() => setEvidenceProduct(null)}
      />

      <ProductComparisonModal
        comparison={comparisonData}
        isOpen={showComparison}
        onClose={() => setShowComparison(false)}
      />

      <IngestionStatusModal
        isOpen={showIngestion}
        onClose={() => setShowIngestion(false)}
      />
    </div>
  );
};
