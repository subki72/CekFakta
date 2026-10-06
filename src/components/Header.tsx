"use client";

import Link from "next/link";
import { useState, useEffect } from "react";
import type { User } from "@supabase/supabase-js";
import { supabase } from "@/lib/supabase";
import { ShieldCheck, Menu, X } from "lucide-react";

export default function Header() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [user, setUser] = useState<User | null>(null);

  useEffect(() => {
    // Check active session
    supabase.auth.getSession().then(({ data: { session } }) => {
      setUser(session?.user ?? null);
    });

    // Listen for auth changes
    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, session) => {
      setUser(session?.user ?? null);
    });

    return () => subscription.unsubscribe();
  }, []);

  const handleLogin = async () => {
    try {
      const { error } = await supabase.auth.signInWithOAuth({
        provider: "google",
        options: {
          redirectTo: `${window.location.origin}/`,
        },
      });
      if (error) {
        alert("Gagal login: " + error.message + "\n(Pastikan Google Provider aktif di Supabase)");
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      alert("Terjadi kesalahan saat login: " + msg);
    }
  };

  const handleLogout = async () => {
    await supabase.auth.signOut();
  };

  return (
    <header className="sticky top-0 z-50 bg-[#f4f0ea] border-b-[4px] border-black">
      <div className="max-w-[1400px] mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-20">
          {/* Logo */}
          <Link href="/" className="flex items-center gap-3 group">
            <div className="w-12 h-12 bg-black flex items-center justify-center text-white border-[3px] border-black shadow-[4px_4px_0px_var(--primary)] group-hover:translate-x-[-2px] group-hover:translate-y-[-2px] group-hover:shadow-[6px_6px_0px_var(--primary)] transition-all">
              <ShieldCheck className="w-7 h-7" />
            </div>
            <span className="text-xl sm:text-2xl font-black uppercase tracking-tighter">
              FactGuard (Cek Fakta)
            </span>
          </Link>

          {/* Desktop Nav */}
          <nav className="hidden md:flex items-center gap-6">
            <Link
              href="/"
              className="text-base font-bold uppercase tracking-wider hover:bg-black hover:text-white px-3 py-1 border-[3px] border-transparent hover:border-black transition-colors"
            >
              Analisis
            </Link>
            <Link
              href="/trending"
              className="text-base font-bold uppercase tracking-wider hover:bg-black hover:text-white px-3 py-1 border-[3px] border-transparent hover:border-black transition-colors"
            >
              Trending
            </Link>
            <Link
              href="/history"
              className="text-base font-bold uppercase tracking-wider hover:bg-black hover:text-white px-3 py-1 border-[3px] border-transparent hover:border-black transition-colors"
            >
              Riwayat
            </Link>
            {user && (
              <Link
                href="/feedback"
                className="text-base font-bold uppercase tracking-wider hover:bg-black hover:text-white px-3 py-1 border-[3px] border-transparent hover:border-black transition-colors"
              >
                Kritik & Saran
              </Link>
            )}
          </nav>

          {/* Auth Section */}
          <div className="flex items-center gap-3">
            <div className="hidden sm:inline-flex">
              {user ? (
                <div className="flex items-center gap-4">
                  <span className="text-sm font-bold uppercase truncate max-w-[120px]">
                    {user.user_metadata?.name || user.email}
                  </span>
                  <button onClick={handleLogout} className="btn-ghost text-sm py-1 px-3">
                    KELUAR
                  </button>
                </div>
              ) : (
                <button onClick={handleLogin} className="btn-primary text-sm py-2">
                  MASUK DENGAN GOOGLE
                </button>
              )}
            </div>

            {/* Mobile menu toggle */}
            <button
              className="md:hidden p-2 border-[3px] border-black bg-white shadow-[4px_4px_0px_#000] active:translate-x-[2px] active:translate-y-[2px] active:shadow-[2px_2px_0px_#000]"
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              aria-label="Toggle menu"
            >
              {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
            </button>
          </div>
        </div>

        {/* Mobile Menu */}
        {mobileMenuOpen && (
          <div className="md:hidden py-6 border-t-[4px] border-black bg-[#f4f0ea]">
            <nav className="flex flex-col gap-4">
              <Link
                href="/"
                className="text-xl font-black uppercase border-[3px] border-black bg-white p-4 shadow-[4px_4px_0px_#000]"
                onClick={() => setMobileMenuOpen(false)}
              >
                Analisis
              </Link>
              <Link
                href="/trending"
                className="text-xl font-black uppercase border-[3px] border-black bg-white p-4 shadow-[4px_4px_0px_#000]"
                onClick={() => setMobileMenuOpen(false)}
              >
                Trending
              </Link>
              <Link
                href="/history"
                className="text-xl font-black uppercase border-[3px] border-black bg-white p-4 shadow-[4px_4px_0px_#000]"
                onClick={() => setMobileMenuOpen(false)}
              >
                Riwayat
              </Link>
              {user && (
                <Link
                  href="/feedback"
                  className="text-xl font-black uppercase border-[3px] border-black bg-white p-4 shadow-[4px_4px_0px_#000]"
                  onClick={() => setMobileMenuOpen(false)}
                >
                  Kritik & Saran
                </Link>
              )}

              {user ? (
                <div className="border-[3px] border-black bg-white p-4 shadow-[4px_4px_0px_#000] flex justify-between items-center">
                  <span className="text-base font-bold uppercase truncate">
                    {user.user_metadata?.name || user.email}
                  </span>
                  <button onClick={handleLogout} className="btn-ghost text-sm py-1 px-3 bg-red-100">
                    KELUAR
                  </button>
                </div>
              ) : (
                <button onClick={handleLogin} className="btn-primary mt-4 w-full">
                  MASUK DENGAN GOOGLE
                </button>
              )}
            </nav>
          </div>
        )}
      </div>
    </header>
  );
}
