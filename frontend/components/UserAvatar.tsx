"use client";

import { User } from "@/lib/auth";

interface UserAvatarProps {
  user: User | null;
  size?: "sm" | "md" | "lg";
  className?: string;
}

const sizeClasses = {
  sm: "w-8 h-8 text-sm",
  md: "w-10 h-10 text-base",
  lg: "w-12 h-12 text-lg",
};

export default function UserAvatar({ user, size = "sm", className = "" }: UserAvatarProps) {
  const getInitial = () => {
    if (!user) return "?";
    if (user.full_name) {
      return user.full_name.charAt(0).toUpperCase();
    }
    if (user.email) {
      return user.email.charAt(0).toUpperCase();
    }
    return "?";
  };

  return (
    <div
      className={`${sizeClasses[size]} bg-gray-900 text-white rounded-full flex items-center justify-center font-medium ${className}`}
    >
      {getInitial()}
    </div>
  );
}
