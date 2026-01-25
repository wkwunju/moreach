"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

export default function Navigation() {
  const router = useRouter();
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [showComingSoon, setShowComingSoon] = useState(false);
  const [comingSoonPlatform, setComingSoonPlatform] = useState("");
  const [user, setUser] = useState<any>(null);
  const [showUserMenu, setShowUserMenu] = useState(false);

  useEffect(() => {
    // Check if user is logged in
    const userStr = localStorage.getItem("user");
    if (userStr) {
      try {
        setUser(JSON.parse(userStr));
      } catch (e) {
        console.error("Failed to parse user data");
      }
    }
  }, []);

  const handleLogout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    setUser(null);
    setShowUserMenu(false);
    router.push("/");
  };

  const handlePlatformClick = (platform: string) => {
    if (platform !== "Instagram") {
      setComingSoonPlatform(platform);
      setShowComingSoon(true);
      setTimeout(() => setShowComingSoon(false), 3000);
    }
  };

  return (
    <>
      {/* Linktree Style Navigation */}
      <nav className="fixed top-6 left-0 right-0 z-50 animate-fade-in flex justify-center px-6">
        <div className="bg-white rounded-full px-8 py-4 shadow-xl max-w-6xl w-full">
          <div className="flex items-center justify-between">
            {/* Logo */}
            <Link href="/" className="text-xl font-black text-gray-900 whitespace-nowrap">
              moreach.ai
            </Link>

            {/* Desktop Menu */}
            <div className="hidden lg:flex items-center gap-8">
              <Link href="/try" className="text-gray-700 hover:text-gray-900 transition font-medium">
                Instagram
              </Link>
              <Link href="/reddit" className="text-gray-700 hover:text-gray-900 transition font-medium">
                Reddit
              </Link>
              <button
                onClick={() => handlePlatformClick("X (Twitter)")}
                className="text-gray-700 hover:text-gray-900 transition font-medium"
              >
                Twitter
              </button>
              <button
                onClick={() => handlePlatformClick("TikTok")}
                className="text-gray-700 hover:text-gray-900 transition font-medium"
              >
                TikTok
              </button>
            </div>

            {/* CTA Buttons / User Menu */}
            <div className="hidden lg:flex items-center gap-3">
              {user ? (
                <div className="relative">
                  <button
                    onClick={() => setShowUserMenu(!showUserMenu)}
                    className="flex items-center gap-2 px-4 py-2.5 text-gray-700 hover:text-gray-900 transition font-medium rounded-full hover:bg-gray-100"
                  >
                    <div className="w-8 h-8 bg-gray-900 text-white rounded-full flex items-center justify-center font-semibold">
                      {user.full_name?.[0]?.toUpperCase() || user.email?.[0]?.toUpperCase()}
                    </div>
                    <span>{user.full_name || user.email}</span>
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7" />
                    </svg>
                  </button>
                  
                  {showUserMenu && (
                    <div className="absolute right-0 mt-2 w-64 bg-white rounded-2xl shadow-xl border border-gray-200 py-2 z-50">
                      <div className="px-4 py-3 border-b border-gray-200">
                        <p className="text-sm font-semibold text-gray-900">{user.full_name}</p>
                        <p className="text-xs text-gray-500">{user.email}</p>
                      </div>
                      <Link
                        href="/reddit"
                        className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-50"
                        onClick={() => setShowUserMenu(false)}
                      >
                        My Campaigns
                      </Link>
                      <button
                        onClick={handleLogout}
                        className="w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-red-50"
                      >
                        Log out
                      </button>
                    </div>
                  )}
                </div>
              ) : (
                <>
                  <Link 
                    href="/login" 
                    className="px-6 py-2.5 text-gray-700 hover:text-gray-900 transition font-medium rounded-full hover:bg-gray-100"
                  >
                    Log in
                  </Link>
                  <Link 
                    href="/register" 
                    className="px-6 py-2.5 bg-gray-900 text-white rounded-full hover:bg-gray-800 transition font-medium"
                  >
                    Sign up free
                  </Link>
                </>
              )}
            </div>

            {/* Mobile Menu Button */}
            <button
              onClick={() => setIsMenuOpen(!isMenuOpen)}
              className="lg:hidden p-2 text-gray-700 hover:text-gray-900"
            >
              <svg
                className="w-6 h-6"
                fill="none"
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth="2"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                {isMenuOpen ? (
                  <path d="M6 18L18 6M6 6l12 12" />
                ) : (
                  <path d="M4 6h16M4 12h16M4 18h16" />
                )}
              </svg>
            </button>
          </div>
        </div>
      </nav>

      {/* Mobile Menu Dropdown */}
      {isMenuOpen && (
        <div className="fixed top-24 left-1/2 -translate-x-1/2 z-40 w-80 lg:hidden animate-fade-in px-6">
          <div className="bg-white rounded-3xl px-6 py-6 shadow-2xl">
            <div className="space-y-4">
              <Link href="/try" className="block text-gray-700 hover:text-gray-900 transition font-medium py-2">
                Instagram
              </Link>
              <Link href="/reddit" className="block text-gray-700 hover:text-gray-900 transition font-medium py-2">
                Reddit
              </Link>
              <button
                onClick={() => handlePlatformClick("X (Twitter)")}
                className="block w-full text-left text-gray-700 hover:text-gray-900 transition font-medium py-2"
              >
                Twitter
              </button>
              <button
                onClick={() => handlePlatformClick("TikTok")}
                className="block w-full text-left text-gray-700 hover:text-gray-900 transition font-medium py-2"
              >
                TikTok
              </button>
              <div className="pt-4 border-t border-gray-200 space-y-3">
                {user ? (
                  <>
                    <div className="px-4 py-3 bg-gray-50 rounded-xl">
                      <p className="text-sm font-semibold text-gray-900">{user.full_name}</p>
                      <p className="text-xs text-gray-500">{user.email}</p>
                    </div>
                    <Link 
                      href="/reddit" 
                      className="block text-center py-3 text-gray-700 hover:text-gray-900 transition font-medium rounded-full hover:bg-gray-100"
                      onClick={() => setIsMenuOpen(false)}
                    >
                      My Campaigns
                    </Link>
                    <button
                      onClick={() => {
                        handleLogout();
                        setIsMenuOpen(false);
                      }}
                      className="w-full text-center py-3 text-red-600 hover:bg-red-50 transition font-medium rounded-full"
                    >
                      Log out
                    </button>
                  </>
                ) : (
                  <>
                    <Link 
                      href="/login" 
                      className="block text-center py-3 text-gray-700 hover:text-gray-900 transition font-medium rounded-full hover:bg-gray-100"
                    >
                      Log in
                    </Link>
                    <Link 
                      href="/register" 
                      className="block text-center py-3 bg-gray-900 text-white rounded-full hover:bg-gray-800 transition font-medium"
                    >
                      Sign up free
                    </Link>
                  </>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Coming Soon Toast */}
      {showComingSoon && (
        <div className="fixed top-28 left-1/2 transform -translate-x-1/2 z-50 animate-fade-in">
          <div className="bg-white px-6 py-4 rounded-full shadow-2xl flex items-center gap-3 border border-gray-200">
            <svg className="w-5 h-5 text-lime-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span className="font-semibold text-gray-900">{comingSoonPlatform} support coming soon!</span>
          </div>
        </div>
      )}
    </>
  );
}

