"use client";

import type { AnalysisResult } from "@/lib/api-client";
import Link from "next/link";
import { AlertTriangle } from "lucide-react";

interface ScoreDisplayProps {
  result: AnalysisResult;
}

function getStampProps(label: string): { text: string; color: string; borderClass: string } {
  switch (label) {
    case "OBJEKTIF":
      return { text: "OBJEKTIF", color: "var(--score-objektif)", borderClass: "border-green-500 text-green-600" };
    case "CENDERUNG_BIAS":
      return { text: "CENDERUNG BIAS", color: "var(--score-bias)", borderClass: "border-yellow-500 text-yellow-600" };
    case "SANGAT_MANIPULATIF":
      return { text: "SANGAT MANIPULATIF", color: "var(--score-manipulatif)", borderClass: "border-red-500 text-red-600" };
    default:
      return { text: label, color: "var(--foreground)", borderClass: "border-black text-black" };
  }
}

export default function ScoreDisplay({ result }: ScoreDisplayProps) {
  const stamp = getStampProps(result.label);
  const displayId = result.analysis_id || result.id || "";

  // Split reasoning into bullet points by finding periods, filtering out empty ones
  const bulletPoints = (result.reasoning || "")
    .split(/(?<=\.)\s+/)
    .filter((point) => point.trim().length > 10);

  return (
    <div className="flex flex-col h-full animate-fade-in-up">
      {/* Stamp Header */}
      <div className="flex flex-col items-center justify-center mb-10 mt-6 relative">
        <div
          className={`animate-stamp inline-block px-8 py-4 border-[6px] rounded-lg shadow-[8px_8px_0px_#000] bg-[#f4f0ea] z-10 ${stamp.borderClass}`}
          style={{ transform: "rotate(-5deg)" }}
        >
          <p className="text-4xl sm:text-5xl font-black uppercase tracking-tighter leading-none m-0 text-center">
            {stamp.text}
          </p>
          <div className="w-full h-1 mt-2 bg-current opacity-30"></div>
          <div className="flex justify-between items-center mt-2 px-1">
             <span className="text-lg font-bold">SKOR: {result.score}/100</span>
             <span className="text-lg font-bold">ID: {displayId.slice(0, 8)}</span>
          </div>
        </div>
      </div>

      {/* Meta Info */}
      <div className="flex flex-wrap gap-2 mb-6 justify-center">
        <span className="px-3 py-1 bg-white border-2 border-black font-bold text-sm uppercase shadow-[2px_2px_0px_#000]">
          {result.detected_language === "id" ? "BAHASA INDONESIA" : "BAHASA INGGRIS"}
        </span>
        {Boolean(result.buzzer_indicators && result.buzzer_indicators.length > 0) && (
          <span className="px-3 py-1 bg-red-100 text-red-700 border-2 border-red-700 font-bold text-sm uppercase shadow-[2px_2px_0px_#000] flex items-center">
            <AlertTriangle className="w-4 h-4 mr-2" /> INDIKASI BUZZER TERDETEKSI
          </span>
        )}
      </div>

      {/* Reasoning (Bullet Points) */}
      <div className="brutal-card p-6 sm:p-8 flex-grow">
        <h3 className="text-xl font-black uppercase mb-4 border-b-4 border-black pb-2">
          Poin Analisis Fakta
        </h3>
        
        <ul className="space-y-4 mb-6">
          {bulletPoints.length > 0 ? (
            bulletPoints.map((point, index) => (
              <li key={`point-${index}-${point.slice(0, 16)}`} className="flex gap-4">
                <span className="flex-shrink-0 w-8 h-8 bg-black text-white font-bold flex items-center justify-center text-lg mt-0.5">
                  {index + 1}
                </span>
                <p className="text-base font-medium leading-relaxed pt-1">
                  {point}
                </p>
              </li>
            ))
          ) : (
             <li className="flex gap-4">
                <span className="flex-shrink-0 w-8 h-8 bg-black text-white font-bold flex items-center justify-center text-lg mt-0.5">
                  &gt;
                </span>
                <p className="text-base font-medium leading-relaxed pt-1">
                  {result.reasoning}
                </p>
              </li>
          )}
        </ul>

        {/* Highlighted Issues */}
        {result.highlighted_issues && result.highlighted_issues.length > 0 && (
          <div className="mt-8 border-t-4 border-black pt-6">
            <h4 className="text-lg font-black uppercase mb-4 text-red-600">
              Kutipan Bermasalah
            </h4>
            <div className="space-y-3">
              {result.highlighted_issues.map((issue, i) => (
                <div
                  key={`${issue}-${i}`}
                  className="bg-red-50 border-l-[6px] border-red-500 p-4 font-bold text-sm"
                >
                  &quot;{issue}&quot;
                </div>
              ))}
            </div>
          </div>
        )}

        <div className="mt-8 text-center pt-4 border-t-4 border-black">
          <Link
            href={`/result/${displayId}`}
            className="btn-ghost w-full block hover:bg-black hover:text-white"
          >
            Lihat Diskusi Komunitas
          </Link>
        </div>
      </div>
    </div>
  );
}
