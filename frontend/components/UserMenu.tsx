"use client";

import { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import { User, logout, getTrialDaysRemaining, isTrialActive } from "@/lib/auth";
import UserAvatar from "./UserAvatar";
import BillingDialog from "./BillingDialog";
import SettingsDialog from "./SettingsDialog";

interface UserMenuProps {
  user: User | null;
  /** Position of the menu dropdown */
  position?: "top" | "bottom";
  /** Called when user logs out */
  onLogout?: () => void;
  /**
   * Called when billing is clicked.
   * If provided, parent manages BillingDialog.
   * If not provided, UserMenu manages BillingDialog internally.
   */
  onBilling?: () => void;
  /** Additional class for the container */
  className?: string;
  /** Show compact version (no user info header in dropdown) */
  compact?: boolean;
}

export default function UserMenu({
  user,
  position = "bottom",
  onLogout,
  onBilling,
  className = "",
  compact = false,
}: UserMenuProps) {
  const router = useRouter();
  const [showMenu, setShowMenu] = useState(false);
  const [showBillingDialog, setShowBillingDialog] = useState(false);
  const [showSettingsDialog, setShowSettingsDialog] = useState(false);
  const [currentUser, setCurrentUser] = useState<User | null>(user);
  const menuRef = useRef<HTMLDivElement>(null);

  // Keep currentUser in sync with prop
  useEffect(() => {
    setCurrentUser(user);
  }, [user]);

  // Close menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setShowMenu(false);
      }
    };

    if (showMenu) {
      document.addEventListener("mousedown", handleClickOutside);
    }

    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [showMenu]);

  const handleLogout = () => {
    logout();
    setShowMenu(false);
    if (onLogout) {
      onLogout();
    }
    router.push("/login");
  };

  const handleSettings = () => {
    setShowMenu(false);
    setShowSettingsDialog(true);
  };

  const handleUserUpdate = (updatedUser: User) => {
    setCurrentUser(updatedUser);
  };

  const handleBilling = () => {
    setShowMenu(false);
    if (onBilling) {
      // Parent manages billing dialog
      onBilling();
    } else {
      // UserMenu manages billing dialog internally
      setShowBillingDialog(true);
    }
  };

  if (!currentUser) return null;

  const dropdownPositionClass = position === "top"
    ? "bottom-full mb-2"
    : "top-full mt-2";

  return (
    <>
      <div ref={menuRef} className={`relative ${className}`}>
        {/* User Button */}
        <button
          onClick={() => setShowMenu(!showMenu)}
          className="w-full flex items-center gap-3 p-3 rounded-xl hover:bg-gray-100 transition-colors text-left"
        >
          <UserAvatar user={currentUser} size="md" />
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-gray-900 truncate">
              {currentUser.full_name || "User"}
            </p>
            <p className="text-xs text-gray-500 truncate">{currentUser.email}</p>
          </div>
          {/* Chevron */}
          <svg
            className={`w-4 h-4 text-gray-400 transition-transform ${showMenu ? "rotate-180" : ""}`}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7" />
          </svg>
        </button>

        {/* Dropdown Menu */}
        {showMenu && (
          <div
            className={`absolute left-0 right-0 ${dropdownPositionClass} bg-white rounded-xl shadow-lg border border-gray-200 overflow-hidden z-50`}
          >
            {/* User Info Header (if not compact) */}
            {!compact && (
              <div className="px-4 py-3 border-b border-gray-100 bg-gray-50">
                <p className="text-sm font-medium text-gray-900 truncate">
                  {currentUser.full_name || "User"}
                </p>
                <p className="text-xs text-gray-500 truncate">{currentUser.email}</p>
                {isTrialActive(currentUser) && (
                  <p className="text-xs text-amber-600 mt-1">
                    {getTrialDaysRemaining(currentUser)} days left in trial
                  </p>
                )}
              </div>
            )}

            {/* Menu Items */}
            <div className="py-1">
              {/* Billing */}
              <button
                onClick={handleBilling}
                className="w-full px-4 py-2.5 text-left text-sm text-gray-700 hover:bg-gray-50 flex items-center gap-3 transition-colors"
              >
                <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" />
                </svg>
                Billing
              </button>

              {/* Settings */}
              <button
                onClick={handleSettings}
                className="w-full px-4 py-2.5 text-left text-sm text-gray-700 hover:bg-gray-50 flex items-center gap-3 transition-colors"
              >
                <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
                Settings
              </button>

              <div className="border-t border-gray-100 my-1"></div>

              {/* Log out */}
              <button
                onClick={handleLogout}
                className="w-full px-4 py-2.5 text-left text-sm text-red-600 hover:bg-red-50 flex items-center gap-3 transition-colors"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                </svg>
                Log out
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Billing Dialog (only when managed internally) */}
      {!onBilling && (
        <BillingDialog
          isOpen={showBillingDialog}
          onClose={() => setShowBillingDialog(false)}
          user={currentUser}
        />
      )}

      {/* Settings Dialog */}
      <SettingsDialog
        isOpen={showSettingsDialog}
        onClose={() => setShowSettingsDialog(false)}
        user={currentUser}
        onUpdate={handleUserUpdate}
      />
    </>
  );
}
