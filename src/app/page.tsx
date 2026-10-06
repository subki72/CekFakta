"use client";

import { useState } from "react";
import Link from "next/link";
import { MessageSquare } from "lucide-react";
import AnalysisForm from "@/components/AnalysisForm";
import ScoreDisplay from "@/components/ScoreDisplay";
import type { AnalysisResult } from "@/lib/api-client";

export default function HomePage() {
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [formKey, setFormKey] = useState(0);

  const handleReset = () => {
    setResult(null);
    setFormKey((prev) => prev + 1);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  return (
    <div className="min-h-[calc(100vh-80px)] flex flex-col md:flex-row">

      {/* Left Column (Input Area) */}
      <div className="w-full md:w-1/2 p-6 sm:p-10 lg:p-14 border-b-4 md:border-b-0 md:border-r-4 border-black bg-white flex flex-col justify-center">

        <div className="max-w-xl mx-auto w-full">
          {/* Hero text */}
          <div className="mb-10 animate-fade-in-up">
            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-black uppercase leading-[0.9] tracking-tighter mb-6 text-black">
              Cek Fakta<br />
              <span className="text-blue-600">Politik.</span>
            </h1>
            <p className="text-lg font-bold text-gray-700 leading-tight border-l-[6px] border-black pl-4">
              AI untuk membongkar narasi manipulatif dan bias dalam berita, opini, atau screenshot media sosial.
            </p>
          </div>

          {/* Analysis Form */}
          <AnalysisForm key={formKey} onResult={setResult} />

          {/* Feature Pills */}
          <div className="flex flex-wrap gap-3 mt-8">
            {["DETEKSI BIAS", "POLA BUZZER", "SKOR 0-100", "BILINGUAL"].map((feature) => (
              <span
                key={feature}
                className="px-3 py-1 bg-black text-white text-sm font-bold uppercase tracking-wider shadow-[2px_2px_0px_var(--primary)]"
              >
                {feature}
              </span>
            ))}
          </div>
        </div>

      </div>

      {/* Right Column (Result Area) */}
      <div className="w-full md:w-1/2 bg-[#f4f0ea] p-6 sm:p-10 lg:p-14 flex items-center justify-center relative">

        {/* Decorative elements for empty state */}
        {!result && (
          <div className="absolute inset-0 flex items-center justify-center pointer-events-none opacity-10">
            <div className="text-[20rem] font-black leading-none transform -rotate-12">
              ?
            </div>
          </div>
        )}

        <div className="w-full max-w-xl relative z-10 flex flex-col justify-center py-10">
          {result ? (
            <div>
              <ScoreDisplay result={result} />
              <div className="mt-8 text-center flex flex-wrap justify-center gap-4">
                <Link
                  href={`/result/${result.analysis_id || result.id || ""}`}
                  className="btn-primary flex items-center gap-2"
                >
                  <MessageSquare className="w-4 h-4" />
                  <span>LIHAT DISKUSI & VOTE</span>
                </Link>
                <button
                  onClick={handleReset}
                  className="btn-secondary"
                >
                  CEK NARASI LAIN
                </button>
              </div>
            </div>
          ) : (
            <div className="brutal-card p-10 text-center animate-fade-in-up">
              <div className="w-24 h-24 bg-black text-white text-5xl font-black flex items-center justify-center rounded-full mx-auto mb-6 shadow-[8px_8px_0px_var(--primary)]">
                !
              </div>
              <h2 className="text-3xl font-black uppercase mb-4">
                Siap Menganalisis
              </h2>
              <p className="text-lg font-medium text-gray-700 leading-tight">
                Masukkan teks, URL, atau gambar untuk melihat hasil penilaian objektivitas yang mendalam dan tajam.
              </p>
            </div>
          )}
        </div>

      </div>

    </div>
  );
}
