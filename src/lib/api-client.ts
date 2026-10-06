/**
 * API Client — Wrapper for communication with the FastAPI backend.
 *
 * Handles base URL resolution, error formatting, and auth token injection.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface APIResponse<T = unknown> {
  success: boolean;
  data?: T;
  message?: string;
  error?: string;
  code?: string;
}

export interface AnalysisResult {
  analysis_id: string;
  id?: string;
  input_type: string;
  extracted_text: string;
  detected_language: string;
  score: number;
  label: "OBJEKTIF" | "CENDERUNG_BIAS" | "SANGAT_MANIPULATIF";
  reasoning: string;
  highlighted_issues: string[];
  buzzer_indicators: string[];
}

export interface AnalysisDetail extends AnalysisResult {
  created_at: string;
  vote_agree: number;
  vote_disagree: number;
  user_vote?: boolean | null;
  comments: CommentData[];
}

export interface CommentData {
  id: string;
  user_name: string;
  content: string;
  created_at: string;
}

export interface TrendingData {
  total_analyses: number;
  average_score: number;
  label_distribution: {
    OBJEKTIF: number;
    CENDERUNG_BIAS: number;
    SANGAT_MANIPULATIF: number;
  };
  recent_articles: {
    title: string;
    source: string;
    score: number;
    label: string;
    created_at: string;
  }[];
}

import { supabase } from "./supabase";

async function getAuthToken(): Promise<string | null> {
  if (typeof window === "undefined") return null;
  const { data: { session } } = await supabase.auth.getSession();
  return session?.access_token || null;
}

async function apiFetch<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<APIResponse<T>> {
  const token = await getAuthToken();
  const headers: Record<string, string> = {
    ...(options.headers as Record<string, string>),
  };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  // Don't set Content-Type for FormData (browser sets it with boundary)
  if (!(options.body instanceof FormData)) {
    headers["Content-Type"] = "application/json";
  }

  try {
    const response = await fetch(`${API_BASE}${endpoint}`, {
      ...options,
      headers,
    });

    const data = await response.json();

    if (!response.ok) {
      return {
        success: false,
        error: data.error || "Terjadi kesalahan. Silakan coba lagi.",
        code: data.code || "UNKNOWN_ERROR",
      };
    }

    return data;
  } catch {
    return {
      success: false,
      error: "Tidak dapat terhubung ke server. Periksa koneksi internet Anda.",
      code: "NETWORK_ERROR",
    };
  }
}

/**
 * Submit text/URL for analysis.
 */
export async function analyzeText(
  inputType: string,
  rawInput: string
): Promise<APIResponse<AnalysisResult>> {
  const formData = new FormData();
  formData.append("input_type", inputType);
  formData.append("raw_input", rawInput);

  return apiFetch<AnalysisResult>("/api/analyze", {
    method: "POST",
    body: formData,
  });
}

/**
 * Submit image for analysis.
 */
export async function analyzeImage(
  file: File
): Promise<APIResponse<AnalysisResult>> {
  const formData = new FormData();
  formData.append("input_type", "IMAGE");
  formData.append("image", file);

  return apiFetch<AnalysisResult>("/api/analyze", {
    method: "POST",
    body: formData,
  });
}

/**
 * Get detailed analysis result by ID.
 */
export async function getAnalysis(
  id: string
): Promise<APIResponse<AnalysisDetail>> {
  return apiFetch<AnalysisDetail>(`/api/analyses/${id}`);
}

/**
 * Get trending dashboard data.
 */
export async function getTrending(): Promise<APIResponse<TrendingData>> {
  return apiFetch<TrendingData>("/api/trending");
}

/**
 * Vote on an analysis.
 */
export async function voteAnalysis(
  analysisId: string,
  isAgree: boolean
): Promise<APIResponse<{ vote_agree: number; vote_disagree: number }>> {
  return apiFetch(`/api/analyses/${analysisId}/vote`, {
    method: "POST",
    body: JSON.stringify({ is_agree: isAgree }),
  });
}

/**
 * Add a comment to an analysis.
 */
export async function addComment(
  analysisId: string,
  content: string
): Promise<APIResponse<CommentData>> {
  return apiFetch(`/api/analyses/${analysisId}/comment`, {
    method: "POST",
    body: JSON.stringify({ content }),
  });
}

export interface AnalysisHistoryItem extends AnalysisResult {
  timestamp: string;
}

/**
 * Fetch analysis history for logged in user.
 */
export async function getHistory(): Promise<AnalysisHistoryItem[] | null> {
  const res = await apiFetch<AnalysisHistoryItem[]>("/api/analyses/history");
  return res.success && res.data ? res.data : null;
}

/**
 * Send user feedback to the backend.
 */
export async function sendFeedback(
  subject: string,
  message: string
): Promise<APIResponse<{ sent: boolean }>> {
  return apiFetch<{ sent: boolean }>("/api/feedback/submit", {
    method: "POST",
    body: JSON.stringify({ subject, message }),
  });
}
