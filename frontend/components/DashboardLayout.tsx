"use client";

import { useEffect, useState } from "react";
import DashboardSidebar from "./DashboardSidebar";

interface DashboardLayoutProps {
  children: React.ReactNode;
}

export default function DashboardLayout({ children }: DashboardLayoutProps) {
  const [user, setUser] = useState<any>(null);

  useEffect(() => {
    const userStr = localStorage.getItem("user");
    if (userStr) {
      try {
        setUser(JSON.parse(userStr));
      } catch (e) {
        console.error("Failed to parse user data");
      }
    }
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

