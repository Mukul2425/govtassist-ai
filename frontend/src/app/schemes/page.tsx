"use client";

import { ExternalLink, Loader2, Search, Shield } from "lucide-react";
import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import { listCategories, listSchemes, type SchemeSummary } from "@/lib/api";

export default function SchemesPage() {
  const [schemes, setSchemes] = useState<SchemeSummary[]>([]);
  const [total, setTotal] = useState(0);
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("");
  const [categories, setCategories] = useState<{ name: string; count: number }[]>([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const data = await listSchemes({
        search: search || undefined,
        category: category || undefined,
        page,
        pageSize: 12,
      });
      setSchemes(data.schemes);
      setTotal(data.total);
    } finally {
      setLoading(false);
    }
  }, [search, category, page]);

  useEffect(() => {
    listCategories().then((d) => setCategories(d.categories)).catch(() => {});
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="border-b border-gray-200 bg-white">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-4">
          <Link href="/" className="flex items-center gap-2 text-navy font-semibold">
            <Shield className="h-5 w-5" /> GovtAssist AI
          </Link>
          <nav className="flex gap-4 text-sm">
            <Link href="/" className="text-gray-600 hover:text-navy">Discover</Link>
            <span className="font-medium text-navy">Browse Schemes</span>
          </nav>
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-4 py-8">
        <h1 className="text-2xl font-bold text-gray-900">Browse Government Schemes</h1>
        <p className="mt-1 text-sm text-gray-500">
          Explore {total}+ central and state government schemes
        </p>

        <div className="mt-6 flex flex-wrap gap-3">
          <div className="relative flex-1 min-w-[200px]">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
            <input
              value={search}
              onChange={(e) => { setSearch(e.target.value); setPage(1); }}
              placeholder="Search schemes..."
              className="w-full rounded-lg border border-gray-300 py-2 pl-10 pr-4 text-sm focus:border-navy focus:outline-none focus:ring-2 focus:ring-navy/20"
            />
          </div>
          <select
            value={category}
            onChange={(e) => { setCategory(e.target.value); setPage(1); }}
            className="rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-navy focus:outline-none"
          >
            <option value="">All Categories</option>
            {categories.map((c) => (
              <option key={c.name} value={c.name}>{c.name} ({c.count})</option>
            ))}
          </select>
        </div>

        {loading ? (
          <div className="flex justify-center py-16">
            <Loader2 className="h-8 w-8 animate-spin text-navy" />
          </div>
        ) : (
          <>
            <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {schemes.map((s) => (
                <div key={s.id} className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm hover:shadow-md transition-shadow">
                  <span className="rounded-full bg-navy/5 px-2 py-0.5 text-xs font-medium text-navy">
                    {s.category}
                  </span>
                  <h3 className="mt-2 font-semibold text-gray-900 line-clamp-2">{s.name}</h3>
                  <p className="mt-1 text-sm text-gray-600 line-clamp-3">{s.short_description}</p>
                  <div className="mt-3 flex items-center justify-between">
                    <span className="text-xs text-gray-400 capitalize">{s.government_level}</span>
                    {s.application_url && (
                      <a
                        href={s.application_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-1 text-xs font-medium text-navy hover:underline"
                      >
                        Apply <ExternalLink className="h-3 w-3" />
                      </a>
                    )}
                  </div>
                </div>
              ))}
            </div>

            {total > 12 && (
              <div className="mt-6 flex justify-center gap-2">
                <button
                  disabled={page <= 1}
                  onClick={() => setPage((p) => p - 1)}
                  className="rounded-lg border px-4 py-2 text-sm disabled:opacity-40"
                >
                  Previous
                </button>
                <span className="flex items-center px-3 text-sm text-gray-500">
                  Page {page} of {Math.ceil(total / 12)}
                </span>
                <button
                  disabled={page >= Math.ceil(total / 12)}
                  onClick={() => setPage((p) => p + 1)}
                  className="rounded-lg border px-4 py-2 text-sm disabled:opacity-40"
                >
                  Next
                </button>
              </div>
            )}
          </>
        )}
      </main>
    </div>
  );
}
