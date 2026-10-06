"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import type { AnalysisResult } from "@/lib/api-client";
import { getHistory } from "@/lib/api-client";
import { supabase } from "@/lib/supabase";

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

function getScoreColor(score: number): string {
  if (score >= 70) return "var(--score-objektif)";
  if (score >= 40) return "var(--score-bias)";
  return "var(--score-manipulatif)";
}

const SESSION_KEY = "factguard_history";

interface HistoryItem extends AnalysisResult {
  timestamp: string;
}

export default function HistoryPage() {
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchHistoryData() {
      const { data: { session } } = await supabase.auth.getSession();
      
      if (session) {
        // User is logged in, fetch from backend
        const backendHistory = await getHistory();
        if (backendHistory) {
          setHistory(backendHistory as HistoryItem[]);
        }
      } else {
        // Guest user, load from sessionStorage
        try {
          const stored = sessionStorage.getItem(SESSION_KEY);
          if (stored) {
            setHistory(JSON.parse(stored));
          }
        } catch {
          // sessionStorage not available
        }
      }
      setLoading(false);
    }
    
    fetchHistoryData();
  }, []);

  if (loading) {
    return <div className="p-16 text-center font-black uppercase text-xl">Memuat riwayat...</div>;
  }

  if (history.length === 0) {
    return (
      <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-16 text-center">
        <div className="text-5xl mb-4">📋</div>
        <h1 className="text-3xl font-black uppercase mb-3">Belum Ada Riwayat</h1>
        <p className="font-medium text-gray-700">
          Riwayat analisis Anda akan muncul di sini. Mulai analisis narasi politik
          untuk melihat hasilnya!
        </p>
        <p className="text-xs mt-4 font-bold text-gray-600">
          💡 Login untuk menyimpan riwayat secara permanen. Sebagai guest, riwayat hanya tersimpan selama sesi browser aktif.
        </p>
        <Link href="/" className="btn-primary inline-block mt-6">
          Mulai Analisis
        </Link>
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      <h1 className="text-3xl sm:text-4xl font-black uppercase mb-2">
        Riwayat <span className="bg-black text-white px-2 py-0.5">Analisis</span>
      </h1>
      <p className="text-sm font-bold uppercase mb-8 text-gray-600">
        {history.length} analisis tercatat dalam sesi ini
      </p>

      <div className="space-y-4">
        {history.map((item, i) => {
          const itemKey = item.analysis_id || item.id || `history-${i}`;
          const extractedText = (item.extracted_text || "").slice(0, 80);
          return (
            <Link
              key={itemKey}
              href={`/result/${item.analysis_id || item.id}`}
              className="brutal-card p-5 flex items-center justify-between gap-4 block hover:translate-x-[-2px] hover:translate-y-[-2px] transition-transform"
            >
              <div className="flex-1 min-w-0">
                <p className="text-base font-bold truncate">
                  {extractedText}...
                </p>
                <p className="text-xs font-bold uppercase mt-1 text-gray-600">
                  {item.input_type} • {item.detected_language === "id" ? "🇮🇩 ID" : "🇬🇧 EN"}{" "}
                  • {item.timestamp}
                </p>
              </div>
              <div className="flex items-center gap-3 flex-shrink-0">
                <span className="text-2xl font-black" style={{ color: getScoreColor(item.score) }}>
                  {item.score}
                </span>
                <span className={`px-3 py-1 text-xs font-black uppercase shadow-[2px_2px_0px_#000] ${getLabelBadgeClass(item.label)}`}>
                  {getLabelDisplay(item.label)}
                </span>
              </div>
            </Link>
          );
        })}
      </div>
    </div>
  );
}

