"use client";

import {
  AlertCircle,
  BookOpen,
  ChevronDown,
  ChevronUp,
  ExternalLink,
  FileText,
  Loader2,
  Search,
  Shield,
  Sparkles,
} from "lucide-react";
import Link from "next/link";
import { useState } from "react";

import type { RecommendationResponse, SchemeRecommendation } from "@/lib/api";
import { getRecommendations } from "@/lib/api";
import { cn, formatIncome, statusColor, statusLabel } from "@/lib/utils";

const EXAMPLE_QUERIES = [
  "I am 23 years old, a graduate from Haryana, and my family income is around ₹4 lakh. Which schemes can I apply for?",
  "I am a farmer in Punjab with 2 acres of land. What government benefits am I eligible for?",
  "I am a woman entrepreneur looking for business loans in Maharashtra.",
  "I am an unemployed graduate aged 28 from Bihar seeking employment support.",
];

function SchemeCard({ scheme }: { scheme: SchemeRecommendation }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="rounded-xl border border-gray-200 bg-white shadow-sm transition-shadow hover:shadow-md">
      <div className="p-5">
        <div className="flex items-start justify-between gap-3">
          <div className="flex-1">
            <h3 className="text-lg font-semibold text-navy">{scheme.scheme_name}</h3>
            <p className="mt-1 text-sm text-gray-600">{scheme.short_description}</p>
          </div>
          <span
            className={cn(
              "shrink-0 rounded-full border px-3 py-1 text-xs font-medium",
              statusColor(scheme.eligibility_status)
            )}
          >
            {statusLabel(scheme.eligibility_status)}
          </span>
        </div>

        <div className="mt-3 flex items-center gap-4 text-sm text-gray-500">
          <span>Score: {scheme.eligibility_score.toFixed(0)}%</span>
          {scheme.missing_information.length > 0 && (
            <span className="text-amber-600">
              {scheme.missing_information.length} field(s) needed
            </span>
          )}
        </div>

        <p className="mt-3 text-sm text-gray-700">{scheme.why_eligible}</p>

        <button
          onClick={() => setExpanded(!expanded)}
          className="mt-3 flex items-center gap-1 text-sm font-medium text-navy hover:text-navy-light"
        >
          {expanded ? (
            <>
              Show less <ChevronUp className="h-4 w-4" />
            </>
          ) : (
            <>
              View details <ChevronDown className="h-4 w-4" />
            </>
          )}
        </button>
      </div>

      {expanded && (
        <div className="border-t border-gray-100 bg-gray-50 px-5 py-4 space-y-4">
          <div>
            <h4 className="flex items-center gap-2 text-sm font-semibold text-gray-800">
              <Sparkles className="h-4 w-4 text-saffron" /> Benefits
            </h4>
            <ul className="mt-2 space-y-1">
              {scheme.benefits.map((b, i) => (
                <li key={i} className="text-sm text-gray-600 flex items-start gap-2">
                  <span className="text-green mt-1">•</span> {b}
                </li>
              ))}
            </ul>
          </div>

          <div>
            <h4 className="flex items-center gap-2 text-sm font-semibold text-gray-800">
              <FileText className="h-4 w-4 text-navy" /> Required Documents
            </h4>
            <ul className="mt-2 space-y-1">
              {scheme.required_documents.map((d, i) => (
                <li key={i} className="text-sm text-gray-600 flex items-start gap-2">
                  <span className="text-navy mt-1">•</span> {d}
                </li>
              ))}
            </ul>
          </div>

          <div>
            <h4 className="flex items-center gap-2 text-sm font-semibold text-gray-800">
              <BookOpen className="h-4 w-4 text-green" /> Application Process
            </h4>
            <p className="mt-2 text-sm text-gray-600">{scheme.application_process}</p>
          </div>

          <div className="flex flex-wrap gap-3 pt-2">
            {scheme.application_url && (
              <a
                href={scheme.application_url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1 rounded-lg bg-navy px-4 py-2 text-sm font-medium text-white hover:bg-navy-light transition-colors"
              >
                Apply Now <ExternalLink className="h-3.5 w-3.5" />
              </a>
            )}
            <a
              href={scheme.official_source_url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1 rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-100 transition-colors"
            >
              Official Source <ExternalLink className="h-3.5 w-3.5" />
            </a>
          </div>
        </div>
      )}
    </div>
  );
}

function ProfileBadge({ label, value }: { label: string; value: string }) {
  return (
    <span className="inline-flex items-center gap-1 rounded-full bg-navy/5 px-3 py-1 text-xs font-medium text-navy">
      <span className="text-gray-500">{label}:</span> {value}
    </span>
  );
}

export default function HomePage() {
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<RecommendationResponse | null>(null);
  const [sessionId, setSessionId] = useState<string | undefined>();

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!query.trim() || loading) return;

    setLoading(true);
    setError(null);

    try {
      const data = await getRecommendations(query.trim(), { sessionId });
      setResult(data);
      setSessionId(data.session_id);
      setQuery("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong");
    } finally {
      setLoading(false);
    }
  }

  function handleFollowUp(question: string) {
    setQuery(question.replace(/^•\s*/, ""));
  }

  function handleExampleClick(example: string) {
    setQuery(example);
    setSessionId(undefined);
    setResult(null);
  }

  function handleNewConversation() {
    setSessionId(undefined);
    setResult(null);
    setQuery("");
  }

  const profile = result?.extracted_profile;

  return (
    <div className="min-h-screen">
      {/* Header */}
      <header className="gradient-header border-b border-gray-200">
        <div className="mx-auto max-w-5xl px-4 py-8">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-navy text-white">
                <Shield className="h-7 w-7" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-navy">GovtAssist AI</h1>
                <p className="text-sm text-gray-600">
                  Discover government schemes you may be eligible for
                </p>
              </div>
            </div>
            <nav className="flex gap-4 text-sm">
              <span className="font-medium text-navy">Discover</span>
              <Link href="/schemes" className="text-gray-600 hover:text-navy">Browse Schemes</Link>
            </nav>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-5xl px-4 py-8">
        {/* Search */}
        <section className="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-gray-900">
            Tell us about yourself
          </h2>
          <p className="mt-1 text-sm text-gray-500">
            Describe your age, state, education, occupation, income, and other details in natural language.
          </p>

          <form onSubmit={handleSubmit} className="mt-4">
            {sessionId && (
              <div className="mb-3 flex items-center justify-between rounded-lg bg-navy/5 px-3 py-2 text-xs text-navy">
                <span>Continuing conversation — profile builds across messages</span>
                <button type="button" onClick={handleNewConversation} className="font-medium hover:underline">
                  New conversation
                </button>
              </div>
            )}
            <textarea
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder={sessionId ? "Add more details, e.g. my income is 4 lakh..." : "e.g. I am a 23-year-old graduate from Haryana with a family income of ₹4 lakh..."}
              rows={3}
              className="w-full rounded-xl border border-gray-300 px-4 py-3 text-sm focus:border-navy focus:outline-none focus:ring-2 focus:ring-navy/20 resize-none"
            />
            <div className="mt-3 flex items-center justify-between">
              <p className="text-xs text-gray-400">
                We only use non-sensitive information. No Aadhaar or personal IDs required.
              </p>
              <button
                type="submit"
                disabled={loading || !query.trim()}
                className="inline-flex items-center gap-2 rounded-xl bg-navy px-6 py-2.5 text-sm font-medium text-white hover:bg-navy-light disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {loading ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" /> Analyzing...
                  </>
                ) : (
                  <>
                    <Search className="h-4 w-4" /> Find Schemes
                  </>
                )}
              </button>
            </div>
          </form>

          {/* Example queries */}
          <div className="mt-5">
            <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">
              Try an example
            </p>
            <div className="mt-2 flex flex-wrap gap-2">
              {EXAMPLE_QUERIES.map((ex, i) => (
                <button
                  key={i}
                  onClick={() => handleExampleClick(ex)}
                  className="rounded-lg border border-gray-200 bg-gray-50 px-3 py-1.5 text-xs text-gray-600 hover:bg-gray-100 hover:border-gray-300 transition-colors text-left max-w-xs truncate"
                  title={ex}
                >
                  {ex.length > 60 ? ex.slice(0, 60) + "..." : ex}
                </button>
              ))}
            </div>
          </div>
        </section>

        {/* Error */}
        {error && (
          <div className="mt-6 flex items-center gap-2 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
            <AlertCircle className="h-4 w-4 shrink-0" />
            {error}
          </div>
        )}

        {/* Results */}
        {result && (
          <div className="mt-8 space-y-6">
            {/* Profile extracted */}
            {profile && Object.keys(profile).length > 0 && (
              <section className="rounded-xl border border-gray-200 bg-white p-5">
                <h3 className="text-sm font-semibold text-gray-800">
                  Extracted Profile
                </h3>
                <div className="mt-3 flex flex-wrap gap-2">
                  {profile.age && <ProfileBadge label="Age" value={`${profile.age} years`} />}
                  {profile.state && <ProfileBadge label="State" value={profile.state} />}
                  {profile.education && (
                    <ProfileBadge label="Education" value={profile.education.replace(/_/g, " ")} />
                  )}
                  {profile.occupation && (
                    <ProfileBadge label="Occupation" value={profile.occupation.replace(/_/g, " ")} />
                  )}
                  {profile.annual_family_income && (
                    <ProfileBadge
                      label="Income"
                      value={formatIncome(profile.annual_family_income)}
                    />
                  )}
                  {profile.gender && <ProfileBadge label="Gender" value={profile.gender} />}
                </div>
              </section>
            )}

            {/* AI Summary */}
            <section className="rounded-xl border border-navy/10 bg-navy/5 p-5">
              <h3 className="flex items-center gap-2 text-sm font-semibold text-navy">
                <Sparkles className="h-4 w-4" /> AI Summary
              </h3>
              <p className="mt-2 text-sm text-gray-700 whitespace-pre-line">
                {result.response_summary}
              </p>
            </section>

            {/* Follow-up questions */}
            {result.follow_up_questions.length > 0 && (
              <section className="rounded-xl border border-amber-200 bg-amber-50 p-5">
                <h3 className="text-sm font-semibold text-amber-800">
                  To improve results, click to answer:
                </h3>
                <div className="mt-2 flex flex-wrap gap-2">
                  {result.follow_up_questions.map((q, i) => (
                    <button
                      key={i}
                      onClick={() => handleFollowUp(q)}
                      className="rounded-lg border border-amber-300 bg-white px-3 py-1.5 text-sm text-amber-800 hover:bg-amber-100 transition-colors"
                    >
                      {q}
                    </button>
                  ))}
                </div>
              </section>
            )}

            {/* Scheme cards */}
            <section>
              <h3 className="text-lg font-semibold text-gray-900">
                Recommended Schemes ({result.recommendations.length})
              </h3>
              <div className="mt-4 space-y-4">
                {result.recommendations.length === 0 ? (
                  <p className="text-sm text-gray-500">
                    No matching schemes found. Try providing more details about your profile.
                  </p>
                ) : (
                  result.recommendations.map((scheme) => (
                    <SchemeCard key={scheme.scheme_id} scheme={scheme} />
                  ))
                )}
              </div>
            </section>

            {/* Disclaimer */}
            <section className="rounded-xl border border-gray-200 bg-gray-50 p-5">
              <p className="text-xs text-gray-500 leading-relaxed">
                <strong>Disclaimer:</strong> {result.disclaimer}
              </p>
            </section>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-gray-200 bg-white mt-12">
        <div className="mx-auto max-w-5xl px-4 py-6 text-center text-xs text-gray-400">
          GovtAssist AI — Built with AI Agents, RAG, and Deterministic Rules Engine
        </div>
      </footer>
    </div>
  );
}
