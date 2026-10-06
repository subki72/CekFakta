import type { Metadata } from "next";
import "./globals.css";
import Header from "@/components/Header";

export const metadata: Metadata = {
  title: "FactGuard AI — Deteksi Objektivitas Narasi Politik",
  description:
    "Analisis objektivitas berita dan narasi politik Indonesia menggunakan AI. Deteksi bias, manipulasi, dan pola buzzer secara otomatis.",
  keywords: [
    "fake news detection",
    "deteksi hoax",
    "objektivitas berita",
    "analisis narasi politik",
    "AI fact checker",
    "buzzer detector",
  ],
  openGraph: {
    title: "FactGuard AI — Deteksi Objektivitas Narasi Politik",
    description:
      "Analisis objektivitas berita dan narasi politik Indonesia menggunakan AI.",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="id" className="h-full antialiased">
      <body className="min-h-full flex flex-col">
        <Header />
        <main className="flex-1">{children}</main>
        <footer className="text-center py-6 text-sm" style={{ color: "var(--foreground-muted)" }}>
          <p>© 2026 FactGuard AI — Deteksi Objektivitas Narasi Politik Indonesia</p>
          <p className="mt-1 text-xs opacity-60">
            Powered by Groq AI • Open Source
          </p>
        </footer>
      </body>
    </html>
  );
}
