import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap"
});

export const metadata: Metadata = {
  title: "moreach.ai - AI-Powered Lead Discovery",
  description: "AI-powered lead discovery across social platforms. Turn online conversations into business opportunities.",
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
      </body>
    </html>
  );
}
