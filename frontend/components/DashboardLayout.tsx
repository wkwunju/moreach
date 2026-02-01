"use client";

import { useEffect, useState } from "react";
import DashboardSidebar from "./DashboardSidebar";
import { getUser, refreshUser, type User } from "@/lib/auth";

interface DashboardLayoutProps {
  children: React.ReactNode;
}

export default function DashboardLayout({ children }: DashboardLayoutProps) {
  const [user, setUser] = useState<User | null>(null);

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

  return (
    <div className="flex h-screen bg-gray-50">
      <DashboardSidebar user={user} />
      <main className="flex-1 ml-64 overflow-auto">
        {children}
      </main>
    </div>
  );
}
