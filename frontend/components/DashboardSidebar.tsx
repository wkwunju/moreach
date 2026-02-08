"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { User, getTrialDaysRemaining, isTrialActive } from "@/lib/auth";
import UserMenu from "./UserMenu";
import BillingDialog from "./BillingDialog";

interface SidebarProps {
  user?: User | null;
  isOpen?: boolean;
  onClose?: () => void;
}

export default function DashboardSidebar({ user, isOpen = false, onClose }: SidebarProps) {
  const pathname = usePathname();
  const [showBillingDialog, setShowBillingDialog] = useState(false);

  const navItems = [
    {
      name: "Reddit",
      href: "/reddit",
      icon: (
        <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
          <path d="M12 0A12 12 0 0 0 0 12a12 12 0 0 0 12 12 12 12 0 0 0 12-12A12 12 0 0 0 12 0zm5.01 4.744c.688 0 1.25.561 1.25 1.249a1.25 1.25 0 0 1-2.498.056l-2.597-.547-.8 3.747c1.824.07 3.48.632 4.674 1.488.308-.309.73-.491 1.207-.491.968 0 1.754.786 1.754 1.754 0 .716-.435 1.333-1.01 1.614a3.111 3.111 0 0 1 .042.52c0 2.694-3.13 4.87-7.004 4.87-3.874 0-7.004-2.176-7.004-4.87 0-.183.015-.366.043-.534A1.748 1.748 0 0 1 4.028 12c0-.968.786-1.754 1.754-1.754.463 0 .898.196 1.207.49 1.207-.883 2.878-1.43 4.744-1.487l.885-4.182a.342.342 0 0 1 .14-.197.35.35 0 0 1 .238-.042l2.906.617a1.214 1.214 0 0 1 1.108-.701zM9.25 12C8.561 12 8 12.562 8 13.25c0 .687.561 1.248 1.25 1.248.687 0 1.248-.561 1.248-1.249 0-.688-.561-1.249-1.249-1.249zm5.5 0c-.687 0-1.248.561-1.248 1.25 0 .687.561 1.248 1.249 1.248.688 0 1.249-.561 1.249-1.249 0-.687-.562-1.249-1.25-1.249zm-5.466 3.99a.327.327 0 0 0-.231.094.33.33 0 0 0 0 .463c.842.842 2.484.913 2.961.913.477 0 2.105-.056 2.961-.913a.361.361 0 0 0 .029-.463.33.33 0 0 0-.464 0c-.547.533-1.684.73-2.512.73-.828 0-1.979-.196-2.512-.73a.326.326 0 0 0-.232-.095z"/>
        </svg>
      ),
      comingSoon: false,
    },
    {
      name: "Instagram",
      href: "/try",
      icon: (
        <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
          <path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zm0-2.163c-3.259 0-3.667.014-4.947.072-4.358.2-6.78 2.618-6.98 6.98-.059 1.281-.073 1.689-.073 4.948 0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98 1.281.058 1.689.072 4.948.072 3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98-1.281-.059-1.69-.073-4.949-.073zm0 5.838c-3.403 0-6.162 2.759-6.162 6.162s2.759 6.163 6.162 6.163 6.162-2.759 6.162-6.163c0-3.403-2.759-6.162-6.162-6.162zm0 10.162c-2.209 0-4-1.79-4-4 0-2.209 1.791-4 4-4s4 1.791 4 4c0 2.21-1.791 4-4 4zm6.406-11.845c-.796 0-1.441.645-1.441 1.44s.645 1.44 1.441 1.44c.795 0 1.439-.645 1.439-1.44s-.644-1.44-1.439-1.44z"/>
        </svg>
      ),
      comingSoon: true,
    },
    {
      name: "Twitter",
      href: "#",
      icon: (
        <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
          <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/>
        </svg>
      ),
      comingSoon: true,
    },
    {
      name: "TikTok",
      href: "#",
      icon: (
        <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
          <path d="M19.59 6.69a4.83 4.83 0 0 1-3.77-4.25V2h-3.45v13.67a2.89 2.89 0 0 1-5.2 1.74 2.89 2.89 0 0 1 2.31-4.64 2.93 2.93 0 0 1 .88.13V9.4a6.84 6.84 0 0 0-1-.05A6.33 6.33 0 0 0 5 20.1a6.34 6.34 0 0 0 10.86-4.43v-7a8.16 8.16 0 0 0 4.77 1.52v-3.4a4.85 4.85 0 0 1-1-.1z"/>
        </svg>
      ),
      comingSoon: true,
    },
  ];

  return (
    <>
      {/* Mobile backdrop */}
      {isOpen && (
        <div
          className="lg:hidden fixed inset-0 bg-black/50 z-40"
          onClick={onClose}
        />
      )}

      {/* Sidebar */}
      <div
        className={`
          w-56 bg-white border-r border-gray-200 flex flex-col h-screen fixed left-0 top-0 z-50
          transition-transform duration-300 ease-in-out
          lg:translate-x-0
          ${isOpen ? "translate-x-0" : "-translate-x-full"}
        `}
      >
        {/* Logo with close button on mobile */}
        <div className="h-14 flex items-center justify-between px-5 border-b border-gray-200">
          <Link href="/" className="text-base font-black text-gray-900">
            moreach.ai
          </Link>
          {/* Close button - only on mobile */}
          <button
            onClick={onClose}
            className="lg:hidden p-2 -mr-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

      {/* Navigation */}
      <div className="flex-1 overflow-y-auto py-4">
        <div className="px-3 mb-4">
          <div className="text-[10px] font-semibold text-gray-500 uppercase tracking-wider px-3 mb-1.5">
            Platforms
          </div>
          <nav className="space-y-0.5">
            {navItems.map((item) => {
              const isActive = pathname === item.href;
              return (
                <Link
                  key={item.name}
                  href={item.comingSoon ? "#" : item.href}
                  onClick={(e) => {
                    if (item.comingSoon) {
                      e.preventDefault();
                    } else {
                      onClose?.(); // Close sidebar on mobile when navigating
                    }
                  }}
                  className={`flex items-center gap-2.5 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                    isActive
                      ? "bg-gray-900 text-white"
                      : item.comingSoon
                      ? "text-gray-400 cursor-not-allowed"
                      : "text-gray-700 hover:bg-gray-100"
                  }`}
                >
                  {item.icon}
                  <span>{item.name}</span>
                  {item.comingSoon && (
                    <span className="ml-auto text-xs bg-gray-100 text-gray-500 px-2 py-0.5 rounded">
                      Soon
                    </span>
                  )}
                </Link>
              );
            })}
          </nav>
        </div>
      </div>

      {/* Subscription Status */}
      {user && (
        <SubscriptionStatus
          user={user}
          onSubscribe={() => setShowBillingDialog(true)}
        />
      )}

      {/* User Menu */}
      <div className="border-t border-gray-200 px-3 py-2">
        <UserMenu
          user={user ?? null}
          position="top"
          compact
          onBilling={() => setShowBillingDialog(true)}
        />
      </div>

      </div>

      {/* Billing Dialog - outside sidebar to avoid transform issues */}
      <BillingDialog
        isOpen={showBillingDialog}
        onClose={() => setShowBillingDialog(false)}
        user={user ?? null}
      />
    </>
  );
}

function SubscriptionStatus({
  user,
  onSubscribe,
}: {
  user: User;
  onSubscribe: () => void;
}) {
  const trialActive = isTrialActive(user);
  const trialDays = getTrialDaysRemaining(user);
  const currentTier = user.subscription_tier;

  // Determine subscription status
  // Support both old format (MONTHLY, ANNUALLY) and new format (STARTER_MONTHLY, etc.)
  const isPaid = currentTier === "MONTHLY" ||
    currentTier === "ANNUALLY" ||
    currentTier?.startsWith("STARTER") ||
    currentTier?.startsWith("GROWTH") ||
    currentTier?.startsWith("PRO");

  const isExpired = currentTier === "EXPIRED" ||
    (currentTier === "FREE_TRIAL" && !trialActive);

  // Get display info based on status
  const getStatusInfo = () => {
    if (isPaid) {
      // Determine plan name and billing cycle
      let tierName = "Pro";
      let billingCycle = "Monthly";

      if (currentTier === "MONTHLY") {
        tierName = "Pro";
        billingCycle = "Monthly";
      } else if (currentTier === "ANNUALLY") {
        tierName = "Pro";
        billingCycle = "Annual";
      } else if (currentTier?.includes("_")) {
        tierName = currentTier.split("_")[0];
        tierName = tierName.charAt(0) + tierName.slice(1).toLowerCase();
        billingCycle = currentTier.includes("ANNUALLY") ? "Annual" : "Monthly";
      }

      return {
        title: `${tierName} Plan`,
        subtitle: `${billingCycle} subscription active`,
        showButton: false,
        bgColor: "bg-green-50",
        iconColor: "text-green-500",
        titleColor: "text-green-700",
        icon: (
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        ),
      };
    }

    if (trialActive) {
      return {
        title: "Free Trial Active",
        subtitle: `${trialDays} day${trialDays !== 1 ? "s" : ""} left in trial. Subscribe to keep real-time monitoring active.`,
        showButton: true,
        bgColor: "bg-orange-50",
        iconColor: "text-orange-500",
        titleColor: "text-orange-700",
        icon: (
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        ),
      };
    }

    if (isExpired) {
      return {
        title: "Trial Expired",
        subtitle: "Subscribe to continue monitoring Reddit for leads.",
        showButton: true,
        bgColor: "bg-red-50",
        iconColor: "text-red-500",
        titleColor: "text-red-700",
        icon: (
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
        ),
      };
    }

    // Fallback: show trial status for FREE_TRIAL or unknown tiers
    if (currentTier === "FREE_TRIAL" || !currentTier) {
      return {
        title: "Free Trial",
        subtitle: "Subscribe to unlock all features.",
        showButton: true,
        bgColor: "bg-orange-50",
        iconColor: "text-orange-500",
        titleColor: "text-orange-700",
        icon: (
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        ),
      };
    }

    return null;
  };

  const status = getStatusInfo();

  // Always show something - fallback to trial if no status
  const displayStatus = status || {
    title: "Free Trial",
    subtitle: "Subscribe to unlock all features.",
    showButton: true,
    bgColor: "bg-orange-50",
    iconColor: "text-orange-500",
    titleColor: "text-orange-700",
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    ),
  };

  return (
    <div className="px-3 pb-2">
      <div className={`${displayStatus.bgColor} rounded-lg p-3`}>
        <div className="flex items-start gap-1.5 mb-1.5">
          <span className={`${displayStatus.iconColor} [&>svg]:w-4 [&>svg]:h-4`}>{displayStatus.icon}</span>
          <span className={`text-sm font-semibold ${displayStatus.titleColor}`}>{displayStatus.title}</span>
        </div>
        <p className="text-xs text-gray-600 mb-2">{displayStatus.subtitle}</p>
        {displayStatus.showButton && (
          <button
            onClick={onSubscribe}
            className="w-full flex items-center justify-center gap-1.5 py-2 bg-orange-500 hover:bg-orange-600 text-white text-sm font-semibold rounded-md transition-colors"
          >
            <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z" />
            </svg>
            Subscribe Now
          </button>
        )}
      </div>
    </div>
  );
}
