import type { Metadata } from "next";
import { Inter } from "next/font/google";
import { Analytics } from "@vercel/analytics/react";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap"
});

export const metadata: Metadata = {
  title: "moreach.ai - AI-Powered Lead Discovery",
  description: "AI-powered lead discovery across social platforms. Turn online conversations into business opportunities.",
  icons: {
    icon: [
      { url: "/favicon.ico" },
      { url: "/favicon-16x16.png", sizes: "16x16", type: "image/png" },
      { url: "/favicon-32x32.png", sizes: "32x32", type: "image/png" },
    ],
    apple: [
      { url: "/apple-touch-icon.png", sizes: "180x180", type: "image/png" },
    ],
  },
  manifest: "/site.webmanifest",
  openGraph: {
    title: "moreach.ai - AI-Powered Lead Discovery",
    description: "AI-powered lead discovery across social platforms. Turn online conversations into business opportunities.",
    type: "website",
    siteName: "moreach.ai",
  },
  twitter: {
    card: "summary_large_image",
    title: "moreach.ai - AI-Powered Lead Discovery",
    description: "AI-powered lead discovery across social platforms. Turn online conversations into business opportunities.",
  },
};

export default function RootLayout({
  children
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={inter.variable}>
        {children}
        <Analytics />
      </body>
    </html>
  );
}
