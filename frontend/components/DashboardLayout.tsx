"use client";

import { useEffect, useState, createContext, useContext } from "react";
import DashboardSidebar from "./DashboardSidebar";
import { getUser, refreshUser, type User } from "@/lib/auth";

// Context for mobile sidebar state
interface SidebarContextType {
  isOpen: boolean;
  setIsOpen: (open: boolean) => void;
}

const SidebarContext = createContext<SidebarContextType>({
  isOpen: false,
  setIsOpen: () => {},
});

export const useSidebar = () => useContext(SidebarContext);

interface DashboardLayoutProps {
  children: React.ReactNode;
  hideSidebar?: boolean;
}

export default function DashboardLayout({ children, hideSidebar = false }: DashboardLayoutProps) {
  const [user, setUser] = useState<User | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);

  useEffect(() => {
    const checkUser = () => {
      const userData = getUser();
      setUser(userData);
    };

    // Initial check from cache (fast, shows UI immediately)
    checkUser();

    // Then fetch fresh user data from backend (especially subscription status)
    // This prevents users from bypassing paywall via localStorage manipulation
    refreshUser().then((freshUser) => {
      if (freshUser) {
        setUser(freshUser);
      }
    });

    // Listen for auth changes
    const handleAuthChange = () => {
      checkUser();
    };

    window.addEventListener("storage", handleAuthChange);
    window.addEventListener("authChange", handleAuthChange);

    return () => {
      window.removeEventListener("storage", handleAuthChange);
      window.removeEventListener("authChange", handleAuthChange);
    };
  }, []);

  // Close sidebar on route change (for mobile)
  useEffect(() => {
    setSidebarOpen(false);
  }, []);

  // When sidebar is hidden, render children directly without the layout wrapper
  if (hideSidebar) {
    return (
      <div className="h-screen bg-gray-50">
        {children}
      </div>
    );
  }

  return (
    <SidebarContext.Provider value={{ isOpen: sidebarOpen, setIsOpen: setSidebarOpen }}>
      <div className="flex h-screen bg-gray-50">
        {/* Mobile Header */}
        <div className="lg:hidden fixed top-0 left-0 right-0 h-14 bg-white border-b border-gray-200 flex items-center px-4 z-40">
          <button
            onClick={() => setSidebarOpen(true)}
            className="p-2 -ml-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 6h16M4 12h16M4 18h16" />
            </svg>
          </button>
          <span className="ml-3 text-lg font-bold text-gray-900">moreach.ai</span>
        </div>

        {/* Sidebar */}
        <DashboardSidebar user={user} isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />

        {/* Main content */}
        <main className="flex-1 lg:ml-56 overflow-auto pt-14 lg:pt-0">
          {children}
        </main>
      </div>
    </SidebarContext.Provider>
  );
}
