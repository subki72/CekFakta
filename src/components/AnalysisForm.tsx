"use client";

import { useState, useRef, useEffect } from "react";
import type { AnalysisResult } from "@/lib/api-client";
import { analyzeText, analyzeImage } from "@/lib/api-client";
import { FileText, Link, Image as ImageIcon, Zap, AlertTriangle } from "lucide-react";

type InputTab = "TEXT" | "URL" | "IMAGE";

interface AnalysisFormProps {
  onResult: (result: AnalysisResult) => void;
}

export default function AnalysisForm({ onResult }: AnalysisFormProps) {
  const [activeTab, setActiveTab] = useState<InputTab>("TEXT");
  const [textInput, setTextInput] = useState("");
  const [urlInput, setUrlInput] = useState("");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Revoke object URL on unmount or previewUrl change to prevent memory leaks
  useEffect(() => {
    return () => {
      if (previewUrl) {
        URL.revokeObjectURL(previewUrl);
      }
    };
  }, [previewUrl]);

  const tabs: { key: InputTab; label: string; icon: React.ReactNode }[] = [
    { key: "TEXT", label: "TEKS", icon: <FileText className="w-5 h-5" /> },
    { key: "URL", label: "LINK", icon: <Link className="w-5 h-5" /> },
    { key: "IMAGE", label: "FOTO", icon: <ImageIcon className="w-5 h-5" /> },
  ];

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      if (previewUrl) {
        URL.revokeObjectURL(previewUrl);
      }
      setSelectedFile(file);
      setPreviewUrl(URL.createObjectURL(file));
    }
  };

  const handleSubmit = async () => {
    setError(null);
    setIsLoading(true);

    try {
      let response;

      if (activeTab === "TEXT") {
        if (!textInput.trim()) {
          setError("Teks tidak boleh kosong.");
          setIsLoading(false);
          return;
        }
        response = await analyzeText("TEXT", textInput);
      } else if (activeTab === "URL") {
        if (!urlInput.trim()) {
          setError("URL tidak boleh kosong.");
          setIsLoading(false);
          return;
        }
        response = await analyzeText("URL", urlInput);
      } else {
        if (!selectedFile) {
          setError("Pilih gambar terlebih dahulu.");
          setIsLoading(false);
          return;
        }
        response = await analyzeImage(selectedFile);
      }

      if (response.success && response.data) {
        onResult(response.data);
        // Save to sessionStorage for guest history
        try {
          const raw = sessionStorage.getItem("factguard_history");
          const existing = raw ? JSON.parse(raw) : [];
          const newItem = {
            ...response.data,
            timestamp: new Date().toLocaleDateString("id-ID", {
              day: "numeric",
              month: "short",
              year: "numeric",
              hour: "2-digit",
              minute: "2-digit",
            }),
          };
          sessionStorage.setItem("factguard_history", JSON.stringify([newItem, ...existing].slice(0, 50)));
        } catch {
          // ignore sessionStorage write errors
        }
        setTextInput("");
        setUrlInput("");
        setSelectedFile(null);
        if (previewUrl) {
          URL.revokeObjectURL(previewUrl);
        }
        setPreviewUrl(null);
      } else {
        setError(response.error || "Terjadi kesalahan. Silakan coba lagi.");
      }
    } catch {
      setError("Tidak dapat terhubung ke server.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="brutal-card p-6 sm:p-8" style={{ background: "var(--accent)" }}>
      {/* Title */}
      <h2 className="text-2xl font-black uppercase mb-6 border-b-4 border-black pb-2 inline-block">
        Input Narasi Politik
      </h2>

      {/* Tab selector */}
      <div className="flex gap-2 mb-6">
        {tabs.map((tab) => (
          <button
            key={tab.key}
            onClick={() => {
              setActiveTab(tab.key);
              setError(null);
            }}
            className={`flex-1 py-3 px-2 text-sm sm:text-base ${
              activeTab === tab.key ? "tab-active" : "tab-inactive"
            }`}
          >
            <span className="mr-2">{tab.icon}</span>
            {tab.label}
          </button>
        ))}
      </div>

      {/* Input area */}
      <div className="bg-white border-4 border-black p-4 shadow-[4px_4px_0px_#000]">
        {activeTab === "TEXT" && (
          <div>
            <textarea
              className="w-full bg-transparent border-none outline-none resize-y min-h-[200px] text-lg font-medium placeholder:text-gray-400 placeholder:font-normal"
              placeholder="Paste narasi berita atau opini politik di sini...&#10;&#10;Contoh: Kutipan pidato, teks postingan medsos, atau isi artikel."
              value={textInput}
              onChange={(e) => setTextInput(e.target.value)}
              id="text-input"
            />
            <div className="border-t-4 border-black mt-4 pt-2 flex justify-between items-center text-sm font-bold uppercase">
              <span>Jumlah Kata</span>
              <span className="bg-black text-white px-2 py-1">
                {textInput.split(/\s+/).filter(Boolean).length}
              </span>
            </div>
          </div>
        )}

        {activeTab === "URL" && (
          <div className="py-8">
            <label className="block font-black text-xl mb-4 uppercase">
              Paste URL Berita
            </label>
            <input
              type="url"
              className="w-full bg-transparent border-b-4 border-black outline-none text-xl font-medium placeholder:text-gray-400 pb-2"
              placeholder="https://contoh.com/berita-politik-terbaru"
              value={urlInput}
              onChange={(e) => setUrlInput(e.target.value)}
              id="url-input"
            />
          </div>
        )}

        {activeTab === "IMAGE" && (
          <div>
            <div
              className="border-4 border-dashed border-black p-8 text-center cursor-pointer hover:bg-gray-100 transition-colors"
              onClick={() => fileInputRef.current?.click()}
              id="image-upload-area"
            >
              {previewUrl ? (
                <div>
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img
                    src={previewUrl}
                    alt="Preview screenshot"
                    className="max-h-48 mx-auto border-4 border-black mb-4 shadow-[4px_4px_0px_#000]"
                  />
                  <p className="text-base font-bold uppercase">
                    {selectedFile?.name}
                  </p>
                  <p className="text-sm font-bold text-gray-500 underline mt-1">
                    Ganti Gambar
                  </p>
                </div>
              ) : (
                <div className="py-8">
                  <ImageIcon className="w-16 h-16 mx-auto mb-4" />
                  <p className="font-black text-xl uppercase mb-2">
                    Klik untuk Upload Screenshot
                  </p>
                  <p className="text-sm font-bold text-gray-500">
                    JPG, PNG, atau WEBP (Maks 5MB)
                  </p>
                </div>
              )}
            </div>
            <input
              ref={fileInputRef}
              type="file"
              accept="image/*"
              className="hidden"
              onChange={handleFileChange}
            />
          </div>
        )}
      </div>

      {/* Error display */}
      {error && (
        <div className="mt-6 p-4 border-4 border-black bg-red-500 text-white font-bold text-lg shadow-[4px_4px_0px_#000] flex items-center gap-2">
          <AlertTriangle className="w-6 h-6" /> {error}
        </div>
      )}

      {/* Submit button */}
      <button
        className="btn-primary w-full mt-6 py-4 flex items-center justify-center gap-3 text-xl"
        onClick={handleSubmit}
        disabled={isLoading}
        id="analyze-btn"
      >
        {isLoading ? (
          <>
            <svg
              className="animate-spin h-6 w-6"
              viewBox="0 0 24 24"
              fill="none"
            >
              <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
              />
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
              />
            </svg>
            MENGANALISIS...
          </>
        ) : (
          <><Zap className="w-6 h-6" /> CEK OBJEKTIVITAS</>
        )}
      </button>
    </div>
  );
}
