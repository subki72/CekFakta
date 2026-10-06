"use client";

import { useState, useEffect } from "react";
import type { User } from "@supabase/supabase-js";
import { supabase } from "@/lib/supabase";
import { sendFeedback } from "@/lib/api-client";
import { useRouter } from "next/navigation";
import { Loader2 } from "lucide-react";

export default function FeedbackPage() {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [subject, setSubject] = useState("");
  const [message, setMessage] = useState("");
  const [status, setStatus] = useState<{ type: "success" | "error"; text: string } | null>(null);
  const router = useRouter();

  useEffect(() => {
    supabase.auth.getSession().then(({ data: { session } }) => {
      setUser(session?.user ?? null);
      setLoading(false);
    });
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!subject.trim() || !message.trim()) {
      setStatus({ type: "error", text: "Judul dan pesan tidak boleh kosong." });
      return;
    }

    setSubmitting(true);
    setStatus(null);

    const res = await sendFeedback(subject, message);
    if (res.success) {
      setStatus({ type: "success", text: "Kritik dan saran berhasil dikirim! Terima kasih." });
      setSubject("");
      setMessage("");
    } else {
      setStatus({ type: "error", text: res.error || "Gagal mengirim pesan." });
    }
    setSubmitting(false);
  };

  if (loading) {
    return (
      <div className="min-h-[calc(100vh-80px)] flex items-center justify-center p-6 bg-[#f4f0ea]">
        <Loader2 className="w-12 h-12 animate-spin mx-auto text-black" />
      </div>
    );
  }

  if (!user) {
    return (
      <div className="min-h-[calc(100vh-80px)] flex items-center justify-center p-6 bg-[#f4f0ea]">
        <div className="bg-white border-[4px] border-black p-8 shadow-[8px_8px_0px_var(--primary)] max-w-md text-center">
          <h2 className="text-3xl font-black mb-4 uppercase">Akses Ditolak</h2>
          <p className="text-lg font-bold mb-6">
            Anda harus login terlebih dahulu untuk mengirimkan kritik dan saran.
          </p>
          <button
            onClick={() => router.push("/")}
            className="btn-primary"
          >
            KEMBALI KE BERANDA
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-[calc(100vh-80px)] bg-[#f4f0ea] p-6 lg:p-12">
      <div className="max-w-3xl mx-auto">
        <h1 className="text-4xl lg:text-5xl font-black uppercase mb-8 border-b-4 border-black pb-4 inline-block">
          Kritik & Saran
        </h1>

        <div className="bg-white border-[4px] border-black p-6 sm:p-10 shadow-[8px_8px_0px_#000]">
          <p className="font-bold text-lg mb-6">
            Punya masukan atau menemukan bug? Sampaikan langsung kepada developer kami!
          </p>

          {status && (
            <div
              className={`p-4 mb-6 border-[3px] border-black font-bold uppercase shadow-[4px_4px_0px_#000] ${
                status.type === "success" ? "bg-green-300" : "bg-red-300"
              }`}
            >
              {status.text}
            </div>
          )}

          <form onSubmit={handleSubmit} className="flex flex-col gap-6">
            <div className="flex flex-col gap-2">
              <label htmlFor="subject" className="font-black text-xl uppercase">
                Topik / Judul
              </label>
              <input
                id="subject"
                type="text"
                value={subject}
                onChange={(e) => setSubject(e.target.value)}
                placeholder="Contoh: Fitur Analisis Error"
                className="w-full border-[3px] border-black p-4 text-lg font-bold focus:outline-none focus:ring-4 focus:ring-blue-300 shadow-[4px_4px_0px_#000] transition-shadow"
                disabled={submitting}
              />
            </div>

            <div className="flex flex-col gap-2">
              <label htmlFor="message" className="font-black text-xl uppercase">
                Pesan
              </label>
              <textarea
                id="message"
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                placeholder="Tuliskan masukan Anda secara detail..."
                className="w-full border-[3px] border-black p-4 text-lg font-bold min-h-[200px] resize-y focus:outline-none focus:ring-4 focus:ring-blue-300 shadow-[4px_4px_0px_#000] transition-shadow"
                disabled={submitting}
              />
            </div>

            <button
              type="submit"
              disabled={submitting}
              className="btn-primary text-xl py-4 mt-4"
            >
              {submitting ? "MENGIRIM..." : "KIRIM PESAN"}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
