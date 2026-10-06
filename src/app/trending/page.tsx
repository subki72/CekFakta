"use client";

import { useEffect, useState } from "react";
import { getTrending } from "@/lib/api-client";
import type { TrendingData } from "@/lib/api-client";

function getLabelBadgeClass(label: string): string {
  switch (label) {
    case "OBJEKTIF": return "badge-objektif";
    case "CENDERUNG_BIAS": return "badge-bias";
    case "SANGAT_MANIPULATIF": return "badge-manipulatif";
    default: return "border-2 border-black bg-gray-100 text-black";
  }
}

function getLabelDisplay(label: string): string {
  switch (label) {
    case "OBJEKTIF": return "Objektif";
    case "CENDERUNG_BIAS": return "Cenderung Bias";
    case "SANGAT_MANIPULATIF": return "Sangat Manipulatif";
    default: return label;
  }
}

function getScoreBarColor(score: number): string {
  if (score >= 70) return "var(--score-objektif)";
  if (score >= 40) return "var(--score-bias)";
  return "var(--score-manipulatif)";
}

export default function TrendingPage() {
  const [data, setData] = useState<TrendingData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      const res = await getTrending();
      if (res.success && res.data) {
        setData(res.data);
      }
      setLoading(false);
    }
    load();
  }, []);

  if (loading) {
    return (
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <h1 className="text-3xl font-black uppercase mb-8">
          Dashboard <span className="bg-black text-white px-2 py-0.5">Trending</span>
        </h1>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">
          {[1, 2, 3].map((i) => (
            <div key={`skeleton-${i}`} className="skeleton h-28" />
          ))}
        </div>
        <div className="skeleton h-64" />
      </div>
    );
  }

  if (!data) {
    return (
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-12 text-center">
        <p className="font-bold text-gray-700">
          Belum ada data trending. Mulai analisis berita untuk melihat dashboard!
        </p>
      </div>
    );
  }

  const total = data.total_analyses || 1;
  const distEntries = Object.entries(data.label_distribution);

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      <h1 className="text-3xl sm:text-4xl font-black uppercase mb-2">
        Dashboard <span className="bg-black text-white px-2 py-0.5">Trending</span>
      </h1>
      <p className="text-sm font-bold uppercase mb-8 text-gray-600">
        Statistik narasi politik yang telah dianalisis
      </p>

      {/* Stats cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-10">
        <div className="brutal-card p-5 animate-fade-in-up">
          <p className="text-xs font-bold uppercase tracking-wider text-gray-600">
            Total Analisis
          </p>
          <p className="text-3xl font-black mt-1 text-black">{data.total_analyses}</p>
        </div>
        <div className="brutal-card p-5 animate-fade-in-up" style={{ animationDelay: "0.1s" }}>
          <p className="text-xs font-bold uppercase tracking-wider text-gray-600">
            Rata-rata Skor
          </p>
          <p className="text-3xl font-black mt-1" style={{ color: getScoreBarColor(data.average_score) }}>
            {data.average_score}
          </p>
        </div>
        <div className="brutal-card p-5 animate-fade-in-up" style={{ animationDelay: "0.2s" }}>
          <p className="text-xs font-bold uppercase tracking-wider text-gray-600">
            Narasi Objektif
          </p>
          <p className="text-3xl font-black mt-1" style={{ color: "var(--score-objektif)" }}>
            {total > 0 ? Math.round((data.label_distribution.OBJEKTIF / total) * 100) : 0}%
          </p>
        </div>
      </div>

      {/* Label distribution bars */}
      <div className="brutal-card p-6 mb-10 animate-fade-in-up" style={{ animationDelay: "0.3s" }}>
        <h2 className="text-base font-black uppercase mb-5">Distribusi Label</h2>
        <div className="space-y-4">
          {distEntries.map(([label, count]) => {
            const pct = total > 0 ? Math.round((Number(count) / total) * 100) : 0;
            return (
              <div key={label}>
                <div className="flex justify-between text-sm mb-1.5">
                  <span className={`px-3 py-0.5 text-xs font-black uppercase shadow-[2px_2px_0px_#000] ${getLabelBadgeClass(label)}`}>
                    {getLabelDisplay(label)}
                  </span>
                  <span className="font-bold text-gray-700">
                    {count} ({pct}%)
                  </span>
                </div>
                <div className="h-3 border-2 border-black overflow-hidden" style={{ background: "var(--background-secondary)" }}>
                  <div
                    className="h-full transition-all duration-1000"
                    style={{
                      width: `${pct}%`,
                      background: label === "OBJEKTIF"
                        ? "var(--score-objektif)"
                        : label === "CENDERUNG_BIAS"
                        ? "var(--score-bias)"
                        : "var(--score-manipulatif)",
                    }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Recent articles */}
      {data.recent_articles.length > 0 && (
        <div className="animate-fade-in-up" style={{ animationDelay: "0.4s" }}>
          <h2 className="text-base font-black uppercase mb-4">Artikel Terbaru dari Portal Berita</h2>
          <div className="space-y-3">
            {data.recent_articles.map((article) => (
              <div
                key={article.title + article.created_at}
                className="brutal-card p-4 flex items-center justify-between gap-4"
              >
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-bold truncate">{article.title || "Tanpa judul"}</p>
                  <p className="text-xs font-bold uppercase mt-1 text-gray-600">
                    {article.source} • {new Date(article.created_at).toLocaleDateString("id-ID")}
                  </p>
                </div>
                <div className="flex items-center gap-3 flex-shrink-0">
                  <span className="text-2xl font-black" style={{ color: getScoreBarColor(article.score) }}>
                    {article.score}
                  </span>
                  <span className={`px-3 py-1 text-xs font-black uppercase shadow-[2px_2px_0px_#000] ${getLabelBadgeClass(article.label)}`}>
                    {getLabelDisplay(article.label)}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
