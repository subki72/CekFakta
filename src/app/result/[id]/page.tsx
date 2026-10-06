"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { getAnalysis, voteAnalysis, addComment } from "@/lib/api-client";
import type { AnalysisDetail } from "@/lib/api-client";
import type { User } from "@supabase/supabase-js";
import { supabase } from "@/lib/supabase";
import ScoreDisplay from "@/components/ScoreDisplay";
import {
  Search,
  ThumbsUp,
  ThumbsDown,
  MessageSquare,
  Send,
  AlertCircle,
  CheckCircle2,
} from "lucide-react";

export default function ResultPage() {
  const params = useParams();
  const id = params.id as string;
  const [data, setData] = useState<AnalysisDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [user, setUser] = useState<User | null>(null);
  const [userVote, setUserVote] = useState<boolean | null>(null);
  const [voteSubmitting, setVoteSubmitting] = useState(false);
  const [commentText, setCommentText] = useState("");
  const [commentSubmitting, setCommentSubmitting] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      const res = await getAnalysis(id);
      if (res.success && res.data) {
        setData(res.data);
        if (typeof res.data.user_vote === "boolean") {
          setUserVote(res.data.user_vote);
        }
      } else {
        setError(res.error || "Analisis tidak ditemukan.");
      }
      setLoading(false);
    }
    if (id) load();

    // Check auth session
    supabase.auth.getSession().then(({ data: { session } }) => {
      setUser(session?.user ?? null);
    });

    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, session) => {
      setUser(session?.user ?? null);
    });

    return () => subscription?.unsubscribe();
  }, [id]);

  const actualId = data?.analysis_id || data?.id || id;

  const handleVote = async (isAgree: boolean) => {
    if (!user) {
      setActionError("Silakan masuk dengan Google terlebih dahulu untuk memberikan vote.");
      return;
    }
    setVoteSubmitting(true);
    setActionError(null);
    try {
      const res = await voteAnalysis(actualId, isAgree);
      if (res.success && res.data) {
        const voteData = res.data;
        setData((prev) =>
          prev
            ? {
                ...prev,
                vote_agree: voteData.vote_agree,
                vote_disagree: voteData.vote_disagree,
              }
            : null
        );
        setUserVote(isAgree);
        setActionSuccess(
          isAgree ? "Terima kasih! Vote 'Setuju' berhasil dicatat." : "Vote 'Tidak Setuju' berhasil dicatat."
        );
        setTimeout(() => setActionSuccess(null), 3500);
      } else {
        setActionError(res.error || "Gagal menyimpan vote.");
      }
    } catch {
      setActionError("Terjadi kesalahan saat memproses vote.");
    } finally {
      setVoteSubmitting(false);
    }
  };

  const handleCommentSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!user) {
      setActionError("Silakan masuk dengan Google terlebih dahulu untuk menulis komentar.");
      return;
    }
    if (!commentText.trim()) return;

    setCommentSubmitting(true);
    setActionError(null);
    try {
      const res = await addComment(actualId, commentText.trim());
      if (res.success && res.data) {
        const newComment = res.data;
        setData((prev) =>
          prev
            ? {
                ...prev,
                comments: [...(prev.comments || []), newComment],
              }
            : null
        );
        setCommentText("");
        setActionSuccess("Komentar Anda berhasil dipublikasikan!");
        setTimeout(() => setActionSuccess(null), 3500);
      } else {
        setActionError(res.error || "Gagal mengirim komentar.");
      }
    } catch {
      setActionError("Terjadi kesalahan saat memproses komentar.");
    } finally {
      setCommentSubmitting(false);
    }
  };

  const handleLogin = async () => {
    try {
      const { error } = await supabase.auth.signInWithOAuth({
        provider: "google",
        options: {
          redirectTo: typeof window !== "undefined" ? window.location.href : "/",
        },
      });
      if (error) {
        alert("Gagal login: " + error.message);
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      alert("Terjadi kesalahan: " + msg);
    }
  };

  if (loading) {
    return (
      <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="skeleton h-48 rounded-none mb-6" />
        <div className="skeleton h-32 rounded-none mb-4" />
        <div className="skeleton h-24 rounded-none" />
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-16 text-center">
        <Search className="w-16 h-16 mx-auto mb-4 text-gray-500" />
        <h1 className="text-xl font-black uppercase mb-3">Analisis Tidak Ditemukan</h1>
        <p style={{ color: "var(--foreground-muted)" }}>{error}</p>
        <Link href="/" className="btn-primary inline-block mt-6">
          Kembali ke Beranda
        </Link>
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      <h1 className="text-3xl font-black uppercase tracking-tight mb-6">
        Hasil <span className="text-[#3b82f6]">Analisis</span>
      </h1>

      {/* Score display */}
      <ScoreDisplay result={data} />

      {/* Extracted text preview */}
      <div className="brutal-card p-6 mt-6">
        <h2 className="text-sm font-black uppercase tracking-wider mb-3">Teks yang Dianalisis</h2>
        <p
          className="text-sm leading-relaxed whitespace-pre-wrap font-medium"
          style={{ color: "var(--foreground-muted)", maxHeight: "240px", overflow: "auto" }}
        >
          {data.extracted_text}
        </p>
      </div>

      {/* Action Notification Toasts */}
      {actionError && (
        <div className="mt-6 p-4 border-[3px] border-black bg-red-100 flex items-center justify-between shadow-[4px_4px_0px_#000]">
          <div className="flex items-center gap-3">
            <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0" />
            <span className="text-sm font-bold text-red-900">{actionError}</span>
          </div>
          {!user && (
            <button
              onClick={handleLogin}
              className="btn-primary text-xs py-1 px-3 bg-red-600 hover:bg-red-700"
            >
              MASUK
            </button>
          )}
        </div>
      )}

      {actionSuccess && (
        <div className="mt-6 p-4 border-[3px] border-black bg-green-100 flex items-center gap-3 shadow-[4px_4px_0px_#000]">
          <CheckCircle2 className="w-5 h-5 text-green-700 flex-shrink-0" />
          <span className="text-sm font-bold text-green-900">{actionSuccess}</span>
        </div>
      )}

      {/* Community section */}
      <div className="brutal-card p-6 mt-6">
        <div className="flex items-center justify-between mb-4 border-b-[3px] border-black pb-3">
          <div className="flex items-center gap-2">
            <MessageSquare className="w-5 h-5" />
            <h2 className="text-base font-black uppercase tracking-wider">Diskusi Komunitas</h2>
          </div>
          <span className="text-xs font-bold uppercase tracking-wider text-gray-600">
            {data.comments?.length || 0} Komentar
          </span>
        </div>

        {/* Votes */}
        <div className="mb-6">
          <p className="text-xs font-bold uppercase tracking-wider mb-2" style={{ color: "var(--foreground-muted)" }}>
            Apakah Anda setuju dengan penilaian AI ini?
          </p>
          <div className="flex flex-wrap items-center gap-3">
            <button
              onClick={() => handleVote(true)}
              disabled={voteSubmitting}
              className={`btn-ghost flex items-center gap-2 text-sm font-black py-2 px-4 transition-all ${
                userVote === true ? "bg-green-100 border-green-600" : ""
              }`}
              style={{ borderColor: "rgba(16, 185, 129, 0.8)" }}
            >
              <ThumbsUp className="w-4 h-4 text-green-600" />
              <span>SETUJU ({data.vote_agree})</span>
            </button>
            <button
              onClick={() => handleVote(false)}
              disabled={voteSubmitting}
              className={`btn-ghost flex items-center gap-2 text-sm font-black py-2 px-4 transition-all ${
                userVote === false ? "bg-red-100 border-red-600" : ""
              }`}
              style={{ borderColor: "rgba(239, 68, 68, 0.8)" }}
            >
              <ThumbsDown className="w-4 h-4 text-red-600" />
              <span>TIDAK SETUJU ({data.vote_disagree})</span>
            </button>
          </div>
        </div>

        {/* Comment form */}
        <form onSubmit={handleCommentSubmit} className="mb-6 pt-4 border-t-[2px] border-dashed border-gray-300">
          <label className="block text-xs font-black uppercase tracking-wider mb-2">
            Tambah Tanggapan / Perspektif Anda
          </label>
          <div className="flex flex-col sm:flex-row gap-2">
            <textarea
              value={commentText}
              onChange={(e) => setCommentText(e.target.value)}
              placeholder={
                user
                  ? "Tulis komentar atau sumber pembanding..."
                  : "Masuk dengan Google untuk ikut berdiskusi..."
              }
              rows={2}
              disabled={commentSubmitting}
              className="input-area text-sm py-2 px-3 flex-1 resize-none"
            />
            {user ? (
              <button
                type="submit"
                disabled={commentSubmitting || !commentText.trim()}
                className="btn-primary flex items-center justify-center gap-2 text-sm py-2 px-4 sm:w-auto"
              >
                <Send className="w-4 h-4" />
                <span>{commentSubmitting ? "KIRIM..." : "KIRIM"}</span>
              </button>
            ) : (
              <button
                type="button"
                onClick={handleLogin}
                className="btn-primary text-sm py-2 px-4 whitespace-nowrap"
              >
                MASUK DENGAN GOOGLE
              </button>
            )}
          </div>
        </form>

        {/* Comments list */}
        {data.comments && data.comments.length > 0 ? (
          <div className="space-y-3">
            {data.comments.map((comment) => (
              <div
                key={comment.id}
                className="p-4 border-[2px] border-black bg-[#faf8f5] shadow-[2px_2px_0px_#000]"
              >
                <div className="flex justify-between items-center mb-1">
                  <span className="text-sm font-black uppercase tracking-wider">
                    {comment.user_name}
                  </span>
                  <span className="text-xs font-medium" style={{ color: "var(--foreground-muted)" }}>
                    {new Date(comment.created_at).toLocaleDateString("id-ID", {
                      day: "numeric",
                      month: "short",
                      year: "numeric",
                    })}
                  </span>
                </div>
                <p className="text-sm font-medium leading-relaxed" style={{ color: "var(--foreground-muted)" }}>
                  {comment.content}
                </p>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-sm font-medium text-center py-4" style={{ color: "var(--foreground-muted)", opacity: 0.7 }}>
            Belum ada komentar. {user ? "Jadilah yang pertama berkomentar!" : "Masuk untuk memulai diskusi."}
          </p>
        )}
      </div>

      {/* Meta info */}
      <div className="text-center mt-6">
        <p className="text-xs font-mono font-medium" style={{ color: "var(--foreground-muted)", opacity: 0.6 }}>
          ID: {actualId} • Dianalisis pada{" "}
          {new Date(data.created_at).toLocaleString("id-ID")}
        </p>
      </div>
    </div>
  );
}
