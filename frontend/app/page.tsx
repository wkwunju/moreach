"use client";

import Navigation from "../components/Navigation";
import GlobeAnimation from "../components/GlobeAnimation";
import Link from "next/link";
import { useState, useEffect, useRef, useCallback } from "react";
import { getUser } from "@/lib/auth";

type Platform = "instagram" | "reddit" | "twitter" | "tiktok";

// Rotating platforms for the hero "Turn [Platform] into Customers"
const HERO_PLATFORMS = [
  { name: "Reddit", color: "#FF4500" },
  { name: "TikTok", color: "#000000" },
  { name: "Instagram", color: "#E4405F" },
  { name: "X/Twitter", color: "#000000" },
] as const;

const SCRAMBLE_CHARS = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz";

function useTextScramble(text: string) {
  const [displayed, setDisplayed] = useState(text);
  const frameRef = useRef<number>(0);
  const prevTextRef = useRef(text);

  const scramble = useCallback((from: string, to: string) => {
    const length = Math.max(from.length, to.length);
    const duration = 600; // total ms
    const startTime = performance.now();

    const step = (now: number) => {
      const elapsed = now - startTime;
      const progress = Math.min(elapsed / duration, 1);

      let result = "";
      for (let i = 0; i < length; i++) {
        const charProgress = Math.max(0, Math.min(1, (progress - i * 0.06) / 0.4));
        if (charProgress >= 1) {
          result += to[i] ?? "";
        } else if (charProgress <= 0) {
          result += from[i] ?? SCRAMBLE_CHARS[Math.floor(Math.random() * SCRAMBLE_CHARS.length)];
        } else {
          result += SCRAMBLE_CHARS[Math.floor(Math.random() * SCRAMBLE_CHARS.length)];
        }
      }
      setDisplayed(result);

      if (progress < 1) {
        frameRef.current = requestAnimationFrame(step);
      } else {
        setDisplayed(to);
      }
    };

    cancelAnimationFrame(frameRef.current);
    frameRef.current = requestAnimationFrame(step);
  }, []);

  useEffect(() => {
    if (text !== prevTextRef.current) {
      scramble(prevTextRef.current, text);
      prevTextRef.current = text;
    }
  }, [text, scramble]);

  useEffect(() => () => cancelAnimationFrame(frameRef.current), []);

  return displayed;
}

function PlatformLogo({ platform }: { platform: string }) {
  const iconSize = "w-8 h-8 md:w-9 md:h-9";
  const boxBase = "w-12 h-12 md:w-14 md:h-14 rounded-2xl flex items-center justify-center shrink-0";
  switch (platform) {
    case "Reddit":
      return (
        <span className={`${boxBase} bg-orange-500`}>
          <svg className={iconSize} fill="white" viewBox="0 0 24 24">
            <path d="M12 0A12 12 0 0 0 0 12a12 12 0 0 0 12 12 12 12 0 0 0 12-12A12 12 0 0 0 12 0zm5.01 4.744c.688 0 1.25.561 1.25 1.249a1.25 1.25 0 0 1-2.498.056l-2.597-.547-.8 3.747c1.824.07 3.48.632 4.674 1.488.308-.309.73-.491 1.207-.491.968 0 1.754.786 1.754 1.754 0 .716-.435 1.333-1.01 1.614a3.111 3.111 0 0 1 .042.52c0 2.694-3.13 4.87-7.004 4.87-3.874 0-7.004-2.176-7.004-4.87 0-.183.015-.366.043-.534A1.748 1.748 0 0 1 4.028 12c0-.968.786-1.754 1.754-1.754.463 0 .898.196 1.207.49 1.207-.883 2.878-1.43 4.744-1.487l.885-4.182a.342.342 0 0 1 .14-.197.35.35 0 0 1 .238-.042l2.906.617a1.214 1.214 0 0 1 1.108-.701zM9.25 12C8.561 12 8 12.562 8 13.25c0 .687.561 1.248 1.25 1.248.687 0 1.248-.561 1.248-1.249 0-.688-.561-1.249-1.249-1.249zm5.5 0c-.687 0-1.248.561-1.248 1.25 0 .687.561 1.248 1.249 1.248.688 0 1.249-.561 1.249-1.249 0-.687-.562-1.249-1.25-1.249zm-5.466 3.99a.327.327 0 0 0-.231.094.33.33 0 0 0 0 .463c.842.842 2.484.913 2.961.913.477 0 2.105-.056 2.961-.913a.361.361 0 0 0 .029-.463.33.33 0 0 0-.464 0c-.547.533-1.684.73-2.512.73-.828 0-1.979-.196-2.512-.73a.326.326 0 0 0-.232-.095z"/>
          </svg>
        </span>
      );
    case "TikTok":
      return (
        <span className={`${boxBase} bg-gradient-to-br from-cyan-400 via-pink-500 to-purple-600`}>
          <svg className={iconSize} fill="white" viewBox="0 0 24 24">
            <path d="M19.59 6.69a4.83 4.83 0 0 1-3.77-4.25V2h-3.45v13.67a2.89 2.89 0 0 1-5.2 1.74 2.89 2.89 0 0 1 2.31-4.64 2.93 2.93 0 0 1 .88.13V9.4a6.84 6.84 0 0 0-1-.05A6.33 6.33 0 0 0 5 20.1a6.34 6.34 0 0 0 10.86-4.43v-7a8.16 8.16 0 0 0 4.77 1.52v-3.4a4.85 4.85 0 0 1-1-.1z"/>
          </svg>
        </span>
      );
    case "Instagram":
      return (
        <span className={`${boxBase} bg-gradient-to-br from-purple-500 via-pink-500 to-orange-500`}>
          <svg className={iconSize} fill="white" viewBox="0 0 24 24">
            <path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zm0-2.163c-3.259 0-3.667.014-4.947.072-4.358.2-6.78 2.618-6.98 6.98-.059 1.281-.073 1.689-.073 4.948 0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98 1.281.058 1.689.072 4.948.072 3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98-1.281-.059-1.69-.073-4.949-.073zm0 5.838c-3.403 0-6.162 2.759-6.162 6.162s2.759 6.163 6.162 6.163 6.162-2.759 6.162-6.163c0-3.403-2.759-6.162-6.162-6.162zm0 10.162c-2.209 0-4-1.79-4-4 0-2.209 1.791-4 4-4s4 1.791 4 4c0 2.21-1.791 4-4 4zm6.406-11.845c-.796 0-1.441.645-1.441 1.44s.645 1.44 1.441 1.44c.795 0 1.439-.645 1.439-1.44s-.644-1.44-1.439-1.44z"/>
          </svg>
        </span>
      );
    case "X":
      return (
        <span className={`${boxBase} bg-black`}>
          <svg className={iconSize} fill="white" viewBox="0 0 24 24">
            <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/>
          </svg>
        </span>
      );
    default:
      return null;
  }
}

export default function HomePage() {
  const [selectedPlatform, setSelectedPlatform] = useState<Platform>("reddit");
  const [billingPeriod, setBillingPeriod] = useState<"monthly" | "annually">("annually");
  const [platformIndex, setPlatformIndex] = useState(0);
  const [isLoggedIn, setIsLoggedIn] = useState(false);

  const scrambledName = useTextScramble(HERO_PLATFORMS[platformIndex].name);

  // Check if user is logged in - redirect CTA links to dashboard
  useEffect(() => {
    const user = getUser();
    setIsLoggedIn(!!user);
  }, []);

  const ctaHref = isLoggedIn ? "/reddit" : "/register";

  // Rotate platforms every 3 seconds
  useEffect(() => {
    const interval = setInterval(() => {
      setPlatformIndex((prev) => (prev + 1) % HERO_PLATFORMS.length);
    }, 3000);

    return () => clearInterval(interval);
  }, []);

  return (
    <div className="min-h-screen bg-white overflow-x-hidden">
      <Navigation />

      {/* Hero Section - Linktree Yellow-Green */}
      <section className="min-h-screen bg-gradient-to-br from-yellow-300 via-lime-300 to-green-300 relative flex items-center">
        <div className="max-w-7xl mx-auto px-6 grid lg:grid-cols-[1.618fr_1fr] gap-12 items-center relative z-10 w-full pt-28 pb-20 md:py-20">
          {/* Left Content */}
          <div className="text-left">
          {/* Main Title - Find Users on [Platform] with AI */}
            <h1 className="font-display text-4xl md:text-5xl lg:text-6xl font-bold mb-6 leading-tight text-gray-900">
              <span className="block">Find Users on</span>
              <span className="block font-display italic">{scrambledName}</span>
              <span className="block">with AI.</span>
          </h1>

          {/* Subtitle */}
            <p className="text-lg md:text-xl text-gray-700 mb-10 leading-relaxed max-w-xl">
              You are building a great product, now you need to reach the right audience. Moreach's AI identifies high-intent signals in communities and posts, and connects them to you.
          </p>

          {/* CTA Buttons */}
            <div className="flex flex-col sm:flex-row gap-4 mb-8">
            <Link
              href={ctaHref}
                className="px-10 py-5 bg-gray-900 text-white text-lg font-bold rounded-full hover:bg-gray-800 transition-all shadow-xl text-center"
            >
              Sign Up for Free
            </Link>
            <Link
              href="/demo"
                className="px-10 py-5 bg-white text-gray-900 text-lg font-bold rounded-full hover:bg-gray-100 transition-all shadow-xl text-center border-2 border-gray-900"
            >
              Request Demo
            </Link>
          </div>

          {/* Trust Indicators */}
            <div className="flex flex-wrap gap-6 text-sm text-gray-800 font-medium">
            <div className="flex items-center gap-2">
                <svg className="w-5 h-5 text-green-800" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
              </svg>
              <span>Free 7-day trial</span>
            </div>
            <div className="flex items-center gap-2">
                <svg className="w-5 h-5 text-green-800" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
              </svg>
              <span>Cancel anytime</span>
              </div>
            </div>
          </div>

          {/* Right Content - Globe Animation */}
          <div className="relative hidden lg:block h-full">
            <GlobeAnimation />
          </div>
        </div>
      </section>

      {/* Platforms Section */}
      <section id="platforms" className="pt-16 pb-8 md:pt-24 md:pb-12 bg-gray-50">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center mb-16 animate-fade-in">
            <h2 className="text-4xl md:text-5xl font-bold text-gray-900 mb-4">
              Choose a platform
            </h2>
            <p className="text-base md:text-lg text-gray-600">
              See how Moreach can help you to grow
            </p>
          </div>

          {/* Platform Cards */}
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            {/* Reddit */}
            <button
              onClick={() => setSelectedPlatform("reddit")}
              className={`rounded-3xl p-8 shadow-xl hover:shadow-2xl transition-all duration-300 group text-left transform hover:-translate-y-3 ${
                selectedPlatform === "reddit" 
                  ? "bg-gradient-to-br from-orange-500 via-red-500 to-orange-600 scale-105 ring-4 ring-orange-300" 
                  : "bg-white border-2 border-gray-200 hover:border-orange-300"
              }`}
            >
              <div className={`w-20 h-20 rounded-3xl flex items-center justify-center mb-6 group-hover:scale-110 group-hover:rotate-6 transition-all ${
                selectedPlatform === "reddit" 
                  ? "bg-white/20 backdrop-blur" 
                  : "bg-orange-500"
              }`}>
                <svg className="w-12 h-12 text-white" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M12 0A12 12 0 0 0 0 12a12 12 0 0 0 12 12 12 12 0 0 0 12-12A12 12 0 0 0 12 0zm5.01 4.744c.688 0 1.25.561 1.25 1.249a1.25 1.25 0 0 1-2.498.056l-2.597-.547-.8 3.747c1.824.07 3.48.632 4.674 1.488.308-.309.73-.491 1.207-.491.968 0 1.754.786 1.754 1.754 0 .716-.435 1.333-1.01 1.614a3.111 3.111 0 0 1 .042.52c0 2.694-3.13 4.87-7.004 4.87-3.874 0-7.004-2.176-7.004-4.87 0-.183.015-.366.043-.534A1.748 1.748 0 0 1 4.028 12c0-.968.786-1.754 1.754-1.754.463 0 .898.196 1.207.49 1.207-.883 2.878-1.43 4.744-1.487l.885-4.182a.342.342 0 0 1 .14-.197.35.35 0 0 1 .238-.042l2.906.617a1.214 1.214 0 0 1 1.108-.701zM9.25 12C8.561 12 8 12.562 8 13.25c0 .687.561 1.248 1.25 1.248.687 0 1.248-.561 1.248-1.249 0-.688-.561-1.249-1.249-1.249zm5.5 0c-.687 0-1.248.561-1.248 1.25 0 .687.561 1.248 1.249 1.248.688 0 1.249-.561 1.249-1.249 0-.687-.562-1.249-1.25-1.249zm-5.466 3.99a.327.327 0 0 0-.231.094.33.33 0 0 0 0 .463c.842.842 2.484.913 2.961.913.477 0 2.105-.056 2.961-.913a.361.361 0 0 0 .029-.463.33.33 0 0 0-.464 0c-.547.533-1.684.73-2.512.73-.828 0-1.979-.196-2.512-.73a.326.326 0 0 0-.232-.095z"/>
                </svg>
              </div>
              <h3 className={`text-xl font-semibold mb-3 ${selectedPlatform === "reddit" ? "text-white" : "text-gray-900"}`}>Reddit</h3>
              <p className={`mb-6 text-base ${selectedPlatform === "reddit" ? "text-orange-50" : "text-gray-600"}`}>
                Engage directly with early adopters. Ideal for authentic community feedback and insights.
              </p>
              <div className={`inline-flex items-center font-bold group-hover:gap-2 transition-all ${
                selectedPlatform === "reddit" ? "text-white" : "text-gray-400"
              }`}>
                <span>{selectedPlatform === "reddit" ? "✓ Selected" : "Learn more"}</span>
                <svg className="w-5 h-5 transform group-hover:translate-x-2 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="3" d="M13 7l5 5m0 0l-5 5m5-5H6" />
                </svg>
              </div>
            </button>

            {/* X (Twitter) */}
            <button
              onClick={() => setSelectedPlatform("twitter")}
              className="bg-gray-100 rounded-3xl p-8 shadow-xl hover:shadow-2xl transition-all duration-300 border-2 border-gray-200 hover:border-gray-900 group text-left transform hover:-translate-y-3"
            >
              <div className="w-20 h-20 bg-black rounded-3xl flex items-center justify-center mb-6 group-hover:scale-110 group-hover:rotate-6 transition-all">
                <svg className="w-11 h-11 text-white" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/>
                </svg>
              </div>
              <h3 className="text-2xl font-bold text-gray-900 mb-3">X (Twitter)</h3>
              <p className="text-gray-600 mb-6 text-base">
                Monitor discussions and competitors. Perfect for tech companies to track market trends.
              </p>
              <div className="inline-flex items-center text-gray-400 font-bold">
                <span>Coming Soon</span>
                <svg className="w-5 h-5 ml-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                </svg>
              </div>
            </button>

            {/* TikTok */}
            <button
              onClick={() => setSelectedPlatform("tiktok")}
              className="bg-gray-100 rounded-3xl p-8 shadow-xl hover:shadow-2xl transition-all duration-300 border-2 border-gray-200 hover:border-pink-400 group text-left transform hover:-translate-y-3"
            >
              <div className="w-20 h-20 bg-gradient-to-br from-cyan-400 via-pink-500 to-purple-600 rounded-3xl flex items-center justify-center mb-6 group-hover:scale-110 group-hover:rotate-6 transition-all shadow-lg">
                <svg className="w-12 h-12 text-white" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M19.59 6.69a4.83 4.83 0 0 1-3.77-4.25V2h-3.45v13.67a2.89 2.89 0 0 1-5.2 1.74 2.89 2.89 0 0 1 2.31-4.64 2.93 2.93 0 0 1 .88.13V9.4a6.84 6.84 0 0 0-1-.05A6.33 6.33 0 0 0 5 20.1a6.34 6.34 0 0 0 10.86-4.43v-7a8.16 8.16 0 0 0 4.77 1.52v-3.4a4.85 4.85 0 0 1-1-.1z"/>
                </svg>
              </div>
              <h3 className="text-2xl font-bold text-gray-900 mb-3">TikTok</h3>
              <p className="text-gray-600 mb-6 text-base">
                Connect with Gen Z through viral video creators. Best for entertainment and trending content.
              </p>
              <div className="inline-flex items-center text-gray-400 font-bold">
                <span>Coming Soon</span>
                <svg className="w-5 h-5 ml-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                </svg>
              </div>
            </button>

            {/* Instagram */}
            <button
              onClick={() => setSelectedPlatform("instagram")}
              className="bg-gray-100 rounded-3xl p-8 shadow-xl hover:shadow-2xl transition-all duration-300 border-2 border-gray-200 hover:border-purple-300 group text-left transform hover:-translate-y-3"
            >
              <div className="w-20 h-20 bg-gradient-to-br from-purple-500 via-pink-500 to-orange-500 rounded-3xl flex items-center justify-center mb-6 shadow-lg">
                <svg className="w-12 h-12 text-white" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zm0-2.163c-3.259 0-3.667.014-4.947.072-4.358.2-6.78 2.618-6.98 6.98-.059 1.281-.073 1.689-.073 4.948 0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98 1.281.058 1.689.072 4.948.072 3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98-1.281-.059-1.69-.073-4.949-.073zm0 5.838c-3.403 0-6.162 2.759-6.162 6.162s2.759 6.163 6.162 6.163 6.162-2.759 6.162-6.163c0-3.403-2.759-6.162-6.162-6.162zm0 10.162c-2.209 0-4-1.79-4-4 0-2.209 1.791-4 4-4s4 1.791 4 4c0 2.21-1.791 4-4 4zm6.406-11.845c-.796 0-1.441.645-1.441 1.44s.645 1.44 1.441 1.44c.795 0 1.439-.645 1.439-1.44s-.644-1.44-1.439-1.44z"/>
                </svg>
              </div>
              <h3 className="text-2xl font-bold text-gray-900 mb-3">Instagram</h3>
              <p className="text-gray-600 mb-6 text-base">
                Discover creators your customers follow. Ideal for visual storytelling and brand partnerships.
              </p>
              <div className="inline-flex items-center text-gray-400 font-semibold">
                <span>Coming Soon</span>
                <svg className="w-5 h-5 ml-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                </svg>
              </div>
            </button>
          </div>
        </div>

        {/* Platform Content - Full Width */}
        <div className="mt-20 md:mt-28">
          {selectedPlatform === "reddit" && (
            <RedditContent />
          )}
          {selectedPlatform === "twitter" && (
            <div className="max-w-7xl mx-auto px-6">
              <ComingSoonContent platform="X (Twitter)" />
          </div>
          )}
          {selectedPlatform === "tiktok" && (
            <div className="max-w-7xl mx-auto px-6">
              <ComingSoonContent platform="TikTok" />
        </div>
      )}
          {selectedPlatform === "instagram" && (
            <div className="max-w-7xl mx-auto px-6">
              <ComingSoonContent platform="Instagram" />
            </div>
          )}
        </div>
      </section>

      {/* Use Cases Section - Only show for Instagram */}
      {false && selectedPlatform === "instagram" && (
      <section id="use-cases" className="py-16 md:py-24 px-6 bg-gray-50">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-4xl md:text-5xl font-bold text-gray-900 mb-4">
              Powerful use cases for modern brands
            </h2>
            <p className="text-lg text-gray-600 max-w-3xl mx-auto">
              From discovery to outreach, moreach.ai streamlines your entire influencer marketing workflow
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            {/* Use Case 1 */}
            <div className="bg-white rounded-2xl p-8 shadow-sm hover:shadow-lg transition">
              <div className="w-12 h-12 bg-blue-100 rounded-xl flex items-center justify-center mb-6">
                <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-3">Intent-Based Discovery</h3>
              <p className="text-gray-600 mb-4">
                Describe your business and constraints in natural language. Our AI understands your intent and finds creators that match your brand values and target audience.
              </p>
              <div className="text-sm text-gray-500 space-y-2">
                <div className="flex items-center gap-2">
                  <span className="text-blue-600">→</span>
                  <span>Natural language search</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-blue-600">→</span>
                  <span>LLM-powered intent parsing</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-blue-600">→</span>
                  <span>Smart constraint matching</span>
                </div>
              </div>
            </div>

            {/* Use Case 2 */}
            <div className="bg-white rounded-2xl p-8 shadow-sm hover:shadow-lg transition">
              <div className="w-12 h-12 bg-purple-100 rounded-xl flex items-center justify-center mb-6">
                <svg className="w-6 h-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-3">Real-Time Enrichment</h3>
              <p className="text-gray-600 mb-4">
                Get instant access to comprehensive creator profiles with engagement metrics, audience demographics, and collaboration history—all updated in real-time.
              </p>
              <div className="text-sm text-gray-500 space-y-2">
                <div className="flex items-center gap-2">
                  <span className="text-purple-600">→</span>
                  <span>Live engagement metrics</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-purple-600">→</span>
                  <span>Audience analysis</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-purple-600">→</span>
                  <span>Performance insights</span>
                </div>
              </div>
            </div>

            {/* Use Case 3 */}
            <div className="bg-white rounded-2xl p-8 shadow-sm hover:shadow-lg transition">
              <div className="w-12 h-12 bg-green-100 rounded-xl flex items-center justify-center mb-6">
                <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-3">Smart Ranking</h3>
              <p className="text-gray-600 mb-4">
                Our vector search technology ranks creators by relevance to your brand, ensuring you connect with influencers who will deliver the best ROI.
              </p>
              <div className="text-sm text-gray-500 space-y-2">
                <div className="flex items-center gap-2">
                  <span className="text-green-600">→</span>
                  <span>AI-powered relevance scoring</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-green-600">→</span>
                  <span>Engagement rate analysis</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-green-600">→</span>
                  <span>Brand fit assessment</span>
                </div>
              </div>
            </div>

            {/* Use Case 4 */}
            <div className="bg-white rounded-2xl p-8 shadow-sm hover:shadow-lg transition">
              <div className="w-12 h-12 bg-orange-100 rounded-xl flex items-center justify-center mb-6">
                <svg className="w-6 h-6 text-orange-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                </svg>
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-3">Audience Insights</h3>
              <p className="text-gray-600 mb-4">
                Understand creator audiences at a deeper level with AI-generated insights about demographics, interests, and engagement patterns.
              </p>
              <div className="text-sm text-gray-500 space-y-2">
                <div className="flex items-center gap-2">
                  <span className="text-orange-600">→</span>
                  <span>Demographic breakdowns</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-orange-600">→</span>
                  <span>Interest mapping</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-orange-600">→</span>
                  <span>Audience overlap detection</span>
                </div>
              </div>
            </div>

            {/* Use Case 5 */}
            <div className="bg-white rounded-2xl p-8 shadow-sm hover:shadow-lg transition">
              <div className="w-12 h-12 bg-pink-100 rounded-xl flex items-center justify-center mb-6">
                <svg className="w-6 h-6 text-pink-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-3">Async Discovery Pipeline</h3>
              <p className="text-gray-600 mb-4">
                Don't wait for results. Our background processing continuously discovers new creators while you work, updating results in real-time.
              </p>
              <div className="text-sm text-gray-500 space-y-2">
                <div className="flex items-center gap-2">
                  <span className="text-pink-600">→</span>
                  <span>Background processing</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-pink-600">→</span>
                  <span>Real-time updates</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-pink-600">→</span>
                  <span>Continuous enrichment</span>
                </div>
              </div>
            </div>

            {/* Use Case 6 */}
            <div className="bg-white rounded-2xl p-8 shadow-sm hover:shadow-lg transition">
              <div className="w-12 h-12 bg-indigo-100 rounded-xl flex items-center justify-center mb-6">
                <svg className="w-6 h-6 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                </svg>
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-3">Direct Outreach</h3>
              <p className="text-gray-600 mb-4">
                Access creator contact information and collaboration history to streamline your outreach process and build meaningful partnerships.
              </p>
              <div className="text-sm text-gray-500 space-y-2">
                <div className="flex items-center gap-2">
                  <span className="text-indigo-600">→</span>
                  <span>Contact information</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-indigo-600">→</span>
                  <span>Collaboration history</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-indigo-600">→</span>
                  <span>Outreach templates</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>
      )}

      {/* Partners Section - Hidden for now */}
      {false && (
      <section id="partners" className="py-16 md:py-24 px-6 bg-white">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <p className="text-sm uppercase tracking-wider text-gray-500 mb-4">Trusted by</p>
            <h2 className="text-4xl md:text-5xl font-bold text-gray-900 mb-4">
              Leading brands and agencies
            </h2>
            <p className="text-lg text-gray-600">
              Join the growing list of companies using moreach.ai to scale their influencer marketing
            </p>
          </div>
        </div>
      </section>
      )}

      {/* Features Section - Only show for Instagram */}
      {false && selectedPlatform === "instagram" && (
      <section id="features" className="py-16 md:py-24 px-6 bg-gradient-to-br from-gray-50 to-white">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-4xl md:text-5xl font-bold text-gray-900 mb-4">
              Everything you need to scale influencer marketing
            </h2>
            <p className="text-lg text-gray-600 max-w-3xl mx-auto">
              Powerful features designed to help you discover, analyze, and connect with the right creators
            </p>
          </div>

          <div className="space-y-24">
            {/* Feature 1 */}
            <div className="grid md:grid-cols-2 gap-12 items-center">
              <div>
                <div className="inline-block px-4 py-2 bg-blue-100 text-blue-700 rounded-full text-sm font-semibold mb-4">
                  DISCOVERY
                </div>
                <h3 className="text-2xl md:text-3xl font-bold text-gray-900 mb-4">
                  AI-powered search that understands your brand
                </h3>
                <p className="text-lg text-gray-600 mb-6">
                  Forget complex filters and endless scrolling. Simply describe your business and requirements in natural language, and let our AI find the perfect creators for you.
                </p>
                <ul className="space-y-3">
                  {[
                    "Natural language query processing",
                    "Intent-based matching algorithms",
                    "Vector similarity search",
                    "Multi-constraint optimization"
                  ].map((feature, index) => (
                    <li key={index} className="flex items-center gap-3 text-gray-700">
                      <svg className="w-5 h-5 text-blue-600 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                      </svg>
                      {feature}
                    </li>
                  ))}
                </ul>
              </div>
              <div className="bg-gradient-to-br from-blue-50 to-purple-50 rounded-2xl p-8 shadow-lg">
                <div className="bg-white rounded-xl p-6 shadow-sm">
                  <div className="text-sm text-gray-500 mb-2">Business Description</div>
                  <div className="text-gray-900 mb-4">
                    "We sell premium hydration mixes for endurance athletes..."
                  </div>
                  <div className="text-sm text-gray-500 mb-2">Constraints</div>
                  <div className="text-gray-900 mb-4">
                    "US-based, 25-40, fitness + trail running, 20k-200k followers"
                  </div>
                  <button className="w-full bg-gray-900 text-white py-3 rounded-lg font-semibold">
                    Launch Discovery
                  </button>
                </div>
              </div>
            </div>

            {/* Feature 2 */}
            <div className="grid md:grid-cols-2 gap-12 items-center">
              <div className="order-2 md:order-1">
                <div className="bg-gradient-to-br from-green-50 to-blue-50 rounded-2xl p-8 shadow-lg">
                  <div className="space-y-4">
                    <div className="bg-white rounded-xl p-4 shadow-sm">
                      <div className="flex items-center justify-between mb-2">
                        <span className="font-semibold text-gray-900">@fitness_mike</span>
                        <span className="text-sm text-green-600 font-semibold">95% match</span>
                      </div>
                      <div className="grid grid-cols-3 gap-4 text-sm">
                        <div>
                          <div className="text-gray-500 text-xs">Followers</div>
                          <div className="font-semibold">125K</div>
                        </div>
                        <div>
                          <div className="text-gray-500 text-xs">Eng. Rate</div>
                          <div className="font-semibold">4.2%</div>
                        </div>
                        <div>
                          <div className="text-gray-500 text-xs">Niche</div>
                          <div className="font-semibold">Running</div>
                        </div>
                      </div>
                    </div>
                    <div className="bg-white rounded-xl p-4 shadow-sm">
                      <div className="flex items-center justify-between mb-2">
                        <span className="font-semibold text-gray-900">@trail_sarah</span>
                        <span className="text-sm text-green-600 font-semibold">92% match</span>
                      </div>
                      <div className="grid grid-cols-3 gap-4 text-sm">
                        <div>
                          <div className="text-gray-500 text-xs">Followers</div>
                          <div className="font-semibold">87K</div>
                        </div>
                        <div>
                          <div className="text-gray-500 text-xs">Eng. Rate</div>
                          <div className="font-semibold">5.8%</div>
                        </div>
                        <div>
                          <div className="text-gray-500 text-xs">Niche</div>
                          <div className="font-semibold">Trail</div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
              <div className="order-1 md:order-2">
                <div className="inline-block px-4 py-2 bg-green-100 text-green-700 rounded-full text-sm font-semibold mb-4">
                  ANALYTICS
                </div>
                <h3 className="text-2xl md:text-3xl font-bold text-gray-900 mb-4">
                  Deep insights and performance metrics
                </h3>
                <p className="text-lg text-gray-600 mb-6">
                  Get comprehensive analytics on every creator, including engagement rates, audience demographics, content performance, and brand fit scores.
                </p>
                <ul className="space-y-3">
                  {[
                    "Real-time engagement tracking",
                    "Audience demographic analysis",
                    "Content performance history",
                    "Brand fit scoring"
                  ].map((feature, index) => (
                    <li key={index} className="flex items-center gap-3 text-gray-700">
                      <svg className="w-5 h-5 text-green-600 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                      </svg>
                      {feature}
                    </li>
                  ))}
                </ul>
              </div>
            </div>

            {/* Feature 3 */}
            <div className="grid md:grid-cols-2 gap-12 items-center">
              <div>
                <div className="inline-block px-4 py-2 bg-purple-100 text-purple-700 rounded-full text-sm font-semibold mb-4">
                  AUTOMATION
                </div>
                <h3 className="text-2xl md:text-3xl font-bold text-gray-900 mb-4">
                  Continuous discovery and enrichment
                </h3>
                <p className="text-lg text-gray-600 mb-6">
                  Our async pipeline continuously discovers new creators and enriches existing profiles in the background, ensuring you always have the freshest data.
                </p>
                <ul className="space-y-3">
                  {[
                    "Background processing pipeline",
                    "Automatic profile updates",
                    "Real-time data synchronization",
                    "Smart notification system"
                  ].map((feature, index) => (
                    <li key={index} className="flex items-center gap-3 text-gray-700">
                      <svg className="w-5 h-5 text-purple-600 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                      </svg>
                      {feature}
                    </li>
                  ))}
                </ul>
              </div>
              <div className="bg-gradient-to-br from-purple-50 to-pink-50 rounded-2xl p-8 shadow-lg">
                <div className="bg-white rounded-xl p-6 shadow-sm">
                  <div className="flex items-center justify-between mb-4">
                    <span className="font-semibold text-gray-900">Discovery Status</span>
                    <span className="px-3 py-1 bg-green-100 text-green-700 rounded-full text-xs font-semibold">
                      PROCESSING
                    </span>
                  </div>
                  <div className="space-y-3">
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center">
                        <svg className="w-4 h-4 text-green-600" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                        </svg>
                      </div>
                      <div className="flex-1">
                        <div className="text-sm font-medium text-gray-900">Intent parsing</div>
                        <div className="text-xs text-gray-500">Completed</div>
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                        <div className="w-4 h-4 border-2 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
                      </div>
                      <div className="flex-1">
                        <div className="text-sm font-medium text-gray-900">Discovering creators</div>
                        <div className="text-xs text-gray-500">In progress...</div>
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 bg-gray-100 rounded-full flex items-center justify-center">
                        <div className="w-4 h-4 border-2 border-gray-300 rounded-full"></div>
                      </div>
                      <div className="flex-1">
                        <div className="text-sm font-medium text-gray-400">Enriching profiles</div>
                        <div className="text-xs text-gray-400">Pending</div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>
      )}

      {/* CTA Section - Only show for Instagram */}
      {false && selectedPlatform === "instagram" && (
      <section className="py-16 md:py-24 px-6 bg-gray-900">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-4xl md:text-5xl font-bold text-white mb-6">
            Ready to transform your influencer marketing?
          </h2>
          <p className="text-base md:text-lg text-gray-300 mb-10">
            Join hundreds of brands using moreach.ai to find and connect with the perfect creators
          </p>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <Link
              href={ctaHref}
              className="px-8 py-4 bg-white text-gray-900 text-xl font-semibold rounded-xl hover:bg-gray-100 transition shadow-lg"
            >
              Sign Up for Free
            </Link>
            <Link
              href="/demo"
              className="px-8 py-4 bg-transparent text-white text-xl font-semibold rounded-xl border-2 border-white hover:bg-white/10 transition"
            >
              Request Demo
            </Link>
          </div>
          <p className="mt-6 text-gray-400 text-sm">
            Free 7-day trial • Cancel anytime
          </p>
        </div>
      </section>
      )}

      {/* Pricing Section */}
      <div id="pricing" className="bg-gray-50 py-10 md:py-16">
        <div className="max-w-6xl mx-auto px-6">
          <div className="text-center mb-10">
            <h3 className="text-4xl md:text-5xl font-bold text-gray-900 mb-4">Simple, transparent pricing</h3>
            <p className="text-lg text-gray-600 mb-8">Choose the plan that fits your needs</p>

            {/* Billing Toggle */}
            <div className="inline-flex items-center bg-gray-100 rounded-full p-1">
              <button
                onClick={() => setBillingPeriod("annually")}
                className={`px-6 py-2 rounded-full text-sm font-semibold transition-all flex items-center gap-2 ${
                  billingPeriod === "annually"
                    ? "bg-white text-gray-900 shadow-sm"
                    : "text-gray-600 hover:text-gray-900"
                }`}
              >
                Annually
                <span className="bg-green-100 text-green-700 text-xs px-2 py-0.5 rounded-full font-bold">Save 3 months</span>
              </button>
              <button
                onClick={() => setBillingPeriod("monthly")}
                className={`px-6 py-2 rounded-full text-sm font-semibold transition-all ${
                  billingPeriod === "monthly"
                    ? "bg-white text-gray-900 shadow-sm"
                    : "text-gray-600 hover:text-gray-900"
                }`}
              >
                Monthly
              </button>
            </div>
          </div>

          <div className="grid md:grid-cols-3 gap-6 lg:gap-8">
            {/* Starter Plan */}
            <div className="bg-white rounded-3xl p-8 border-2 border-orange-300 hover:border-orange-400 transition-all hover:shadow-xl flex flex-col relative overflow-hidden">
              {/* Free Trial badge */}
              <div className="absolute top-6 right-6 bg-orange-100 text-orange-600 px-3 py-1 rounded-full text-sm font-semibold">
                7-Day Free Trial
              </div>

              <div className="mb-6">
                <h4 className="text-xl font-semibold text-gray-500 mb-2">Starter</h4>
                <div className="flex items-baseline gap-2">
                  {billingPeriod === "annually" && (
                    <span className="text-2xl font-bold text-gray-400 line-through">$15</span>
                  )}
                  <span className="text-5xl font-bold text-gray-900">${billingPeriod === "monthly" ? "15" : "11"}</span>
                  <span className="text-gray-500 font-medium">/month</span>
                </div>
                {billingPeriod === "annually" && (
                  <p className="text-sm text-green-600 font-medium mt-1">Billed $132/year (Save $48)</p>
                )}
              </div>

              {/* Variable features */}
              <ul className="space-y-3 mb-6">
                <li className="flex items-start gap-3">
                  <svg className="w-5 h-5 text-green-500 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
                  </svg>
                  <span className="text-gray-700"><strong>1</strong> business profile</span>
                </li>
                <li className="flex items-start gap-3">
                  <svg className="w-5 h-5 text-green-500 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
                  </svg>
                  <span className="text-gray-700">Up to <strong>15</strong> subreddits</span>
                </li>
                <li className="flex items-start gap-3">
                  <svg className="w-5 h-5 text-green-500 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
                  </svg>
                  <span className="text-gray-700">Leads refresh <strong>twice a day</strong></span>
                </li>
                <li className="flex items-start gap-3">
                  <svg className="w-5 h-5 text-green-500 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
                  </svg>
                  <span className="text-gray-700"><strong>3,000</strong> leads/month</span>
                </li>
                <li className="flex items-start gap-3">
                  <svg className="w-5 h-5 text-green-500 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
                  </svg>
                  <span className="text-gray-700">Early access to <strong>X, TikTok & Instagram</strong> (March 2026)</span>
                </li>
              </ul>

              {/* Included features */}
              <div className="border-t border-gray-200 pt-6 mt-auto">
                <p className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-3">Included</p>
                <ul className="space-y-2">
                  <li className="flex items-center gap-2 text-sm text-gray-600">
                    <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
                    </svg>
                    AI-generated comments
                  </li>
                  <li className="flex items-center gap-2 text-sm text-gray-600">
                    <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
                    </svg>
                    AI-generated DMs
                  </li>
                  <li className="flex items-center gap-2 text-sm text-gray-600">
                    <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
                    </svg>
                    Community Relevancy Score
                  </li>
                  <li className="flex items-center gap-2 text-sm text-gray-600">
                    <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
                    </svg>
                    Post Relevancy Score
                  </li>
                </ul>
              </div>

              <Link
                href={ctaHref}
                className="block w-full py-4 text-center bg-gray-900 text-white font-semibold rounded-xl hover:bg-gray-800 transition mt-6"
              >
                Start 7-Day Free Trial
              </Link>
            </div>

            {/* Growth Plan */}
            <div className="bg-gradient-to-br from-orange-500 to-red-500 rounded-3xl p-8 text-white relative overflow-hidden hover:shadow-xl transition-all flex flex-col">
              {/* Popular badge */}
              <div className="absolute top-6 right-6 bg-white/20 backdrop-blur-sm px-3 py-1 rounded-full text-sm font-semibold">
                Most Popular
              </div>

              <div className="mb-6">
                <h4 className="text-xl font-semibold text-orange-100 mb-2">Growth</h4>
                <div className="flex items-baseline gap-2">
                  {billingPeriod === "annually" && (
                    <span className="text-2xl font-bold text-white/50 line-through">$39</span>
                  )}
                  <span className="text-5xl font-bold">${billingPeriod === "monthly" ? "39" : "30"}</span>
                  <span className="text-orange-100 font-medium">/month</span>
                </div>
                {billingPeriod === "annually" && (
                  <p className="text-sm text-white font-medium mt-1">Billed $360/year (Save $108)</p>
                )}
              </div>

              {/* Variable features */}
              <ul className="space-y-3 mb-6">
                <li className="flex items-start gap-3">
                  <svg className="w-5 h-5 text-white mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
                  </svg>
                  <span><strong>3</strong> business profiles</span>
                </li>
                <li className="flex items-start gap-3">
                  <svg className="w-5 h-5 text-white mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
                  </svg>
                  <span>Up to <strong>20</strong> subreddits each</span>
                </li>
                <li className="flex items-start gap-3">
                  <svg className="w-5 h-5 text-white mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
                  </svg>
                  <span><strong>7×24</strong> real-time refresh</span>
                </li>
                <li className="flex items-start gap-3">
                  <svg className="w-5 h-5 text-white mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
                  </svg>
                  <span><strong>9,000</strong> leads/month</span>
                </li>
                <li className="flex items-start gap-3">
                  <svg className="w-5 h-5 text-white mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
                  </svg>
                  <span>Early access to <strong>X, TikTok & Instagram</strong> (March 2026)</span>
                </li>
              </ul>

              {/* Included features */}
              <div className="border-t border-white/20 pt-6 mt-auto">
                <p className="text-xs font-semibold text-white/60 uppercase tracking-wide mb-3">Included</p>
                <ul className="space-y-2">
                  <li className="flex items-center gap-2 text-sm text-white/80">
                    <svg className="w-4 h-4 text-white/60" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
                    </svg>
                    AI-generated comments
                  </li>
                  <li className="flex items-center gap-2 text-sm text-white/80">
                    <svg className="w-4 h-4 text-white/60" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
                    </svg>
                    AI-generated DMs
                  </li>
                  <li className="flex items-center gap-2 text-sm text-white/80">
                    <svg className="w-4 h-4 text-white/60" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
                    </svg>
                    Community Relevancy Score
                  </li>
                  <li className="flex items-center gap-2 text-sm text-white/80">
                    <svg className="w-4 h-4 text-white/60" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
                    </svg>
                    Post Relevancy Score
                  </li>
                </ul>
              </div>

              <Link
                href={ctaHref}
                className="block w-full py-4 text-center bg-white text-orange-600 font-semibold rounded-xl hover:bg-orange-50 transition mt-6"
              >
                Get Started
              </Link>
            </div>

            {/* Pro Plan */}
            <div className="bg-gray-900 rounded-3xl p-8 text-white relative overflow-hidden hover:shadow-xl transition-all flex flex-col">
              {/* Best for Teams badge */}
              <div className="absolute top-6 right-6 bg-white/10 backdrop-blur-sm px-3 py-1 rounded-full text-sm font-semibold text-gray-300">
                Best for Teams
              </div>

              <div className="mb-6">
                <h4 className="text-xl font-semibold text-gray-400 mb-2">Pro</h4>
                <div className="flex items-baseline gap-2">
                  {billingPeriod === "annually" && (
                    <span className="text-2xl font-bold text-gray-500 line-through">$99</span>
                  )}
                  <span className="text-5xl font-bold">${billingPeriod === "monthly" ? "99" : "75"}</span>
                  <span className="text-gray-400 font-medium">/month</span>
                </div>
                {billingPeriod === "annually" && (
                  <p className="text-sm text-green-400 font-medium mt-1">Billed $900/year (Save $288)</p>
                )}
              </div>

              {/* Variable features */}
              <ul className="space-y-3 mb-6">
                <li className="flex items-start gap-3">
                  <svg className="w-5 h-5 text-green-400 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
                  </svg>
                  <span>Up to <strong>10</strong> business profiles</span>
                </li>
                <li className="flex items-start gap-3">
                  <svg className="w-5 h-5 text-green-400 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
                  </svg>
                  <span><strong>Unlimited</strong> subreddits</span>
                </li>
                <li className="flex items-start gap-3">
                  <svg className="w-5 h-5 text-green-400 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
                  </svg>
                  <span><strong>7×24</strong> real-time refresh</span>
                </li>
                <li className="flex items-start gap-3">
                  <svg className="w-5 h-5 text-green-400 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
                  </svg>
                  <span><strong>30,000</strong> leads/month</span>
                </li>
                <li className="flex items-start gap-3">
                  <svg className="w-5 h-5 text-green-400 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
                  </svg>
                  <span>Early access to <strong>X, TikTok & Instagram</strong> (March 2026)</span>
                </li>
              </ul>

              {/* Included features */}
              <div className="border-t border-gray-700 pt-6 mt-auto">
                <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-3">Included</p>
                <ul className="space-y-2">
                  <li className="flex items-center gap-2 text-sm text-gray-400">
                    <svg className="w-4 h-4 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
                    </svg>
                    AI-generated comments
                  </li>
                  <li className="flex items-center gap-2 text-sm text-gray-400">
                    <svg className="w-4 h-4 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
                    </svg>
                    AI-generated DMs
                  </li>
                  <li className="flex items-center gap-2 text-sm text-gray-400">
                    <svg className="w-4 h-4 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
                    </svg>
                    Community Relevancy Score
                  </li>
                  <li className="flex items-center gap-2 text-sm text-gray-400">
                    <svg className="w-4 h-4 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
                    </svg>
                    Post Relevancy Score
                  </li>
                </ul>
              </div>

              <Link
                href={ctaHref}
                className="block w-full py-4 text-center bg-white text-gray-900 font-semibold rounded-xl hover:bg-gray-100 transition mt-6"
              >
                Get Started
              </Link>
            </div>
          </div>
        </div>
      </div>

      {/* Footer - Linktree Style */}
      <footer className="py-16 px-6 bg-gradient-to-br from-gray-50 to-purple-50">
        <div className="max-w-7xl mx-auto">
          <div className="grid md:grid-cols-4 gap-12 mb-12">
            <div className="md:col-span-2">
              <div className="text-4xl font-black bg-gradient-to-r from-orange-600 to-purple-600 bg-clip-text text-transparent mb-6">
                moreach.ai
              </div>
              <p className="text-gray-700 text-lg mb-6 leading-relaxed">
                AI-powered lead discovery across social platforms. Turn online conversations into business opportunities.
              </p>
              <div className="flex gap-4">
                <a href="#" className="w-12 h-12 bg-white rounded-full flex items-center justify-center shadow-lg hover:shadow-xl transition-all hover:scale-110 group">
                  <svg className="w-6 h-6 text-gray-600 group-hover:text-orange-600 transition" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M8.29 20.251c7.547 0 11.675-6.253 11.675-11.675 0-.178 0-.355-.012-.53A8.348 8.348 0 0022 5.92a8.19 8.19 0 01-2.357.646 4.118 4.118 0 001.804-2.27 8.224 8.224 0 01-2.605.996 4.107 4.107 0 00-6.993 3.743 11.65 11.65 0 01-8.457-4.287 4.106 4.106 0 001.27 5.477A4.072 4.072 0 012.8 9.713v.052a4.105 4.105 0 003.292 4.022 4.095 4.095 0 01-1.853.07 4.108 4.108 0 003.834 2.85A8.233 8.233 0 012 18.407a11.616 11.616 0 006.29 1.84" />
                  </svg>
                </a>
                <a href="#" className="w-12 h-12 bg-white rounded-full flex items-center justify-center shadow-lg hover:shadow-xl transition-all hover:scale-110 group">
                  <svg className="w-6 h-6 text-gray-600 group-hover:text-orange-600 transition" fill="currentColor" viewBox="0 0 24 24">
                    <path fillRule="evenodd" d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z" clipRule="evenodd" />
                  </svg>
                </a>
                <a href="#" className="w-12 h-12 bg-white rounded-full flex items-center justify-center shadow-lg hover:shadow-xl transition-all hover:scale-110 group">
                  <svg className="w-6 h-6 text-gray-600 group-hover:text-orange-600 transition" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M12 0A12 12 0 0 0 0 12a12 12 0 0 0 12 12 12 12 0 0 0 12-12A12 12 0 0 0 12 0zm5.01 4.744c.688 0 1.25.561 1.25 1.249a1.25 1.25 0 0 1-2.498.056l-2.597-.547-.8 3.747c1.824.07 3.48.632 4.674 1.488.308-.309.73-.491 1.207-.491.968 0 1.754.786 1.754 1.754 0 .716-.435 1.333-1.01 1.614a3.111 3.111 0 0 1 .042.52c0 2.694-3.13 4.87-7.004 4.87-3.874 0-7.004-2.176-7.004-4.87 0-.183.015-.366.043-.534A1.748 1.748 0 0 1 4.028 12c0-.968.786-1.754 1.754-1.754.463 0 .898.196 1.207.49 1.207-.883 2.878-1.43 4.744-1.487l.885-4.182a.342.342 0 0 1 .14-.197.35.35 0 0 1 .238-.042l2.906.617a1.214 1.214 0 0 1 1.108-.701zM9.25 12C8.561 12 8 12.562 8 13.25c0 .687.561 1.248 1.25 1.248.687 0 1.248-.561 1.248-1.249 0-.688-.561-1.249-1.249-1.249zm5.5 0c-.687 0-1.248.561-1.248 1.25 0 .687.561 1.248 1.249 1.248.688 0 1.249-.561 1.249-1.249 0-.687-.562-1.249-1.25-1.249zm-5.466 3.99a.327.327 0 0 0-.231.094.33.33 0 0 0 0 .463c.842.842 2.484.913 2.961.913.477 0 2.105-.056 2.961-.913a.361.361 0 0 0 .029-.463.33.33 0 0 0-.464 0c-.547.533-1.684.73-2.512.73-.828 0-1.979-.196-2.512-.73a.326.326 0 0 0-.232-.095z"/>
                  </svg>
                </a>
              </div>
            </div>
            <div>
              <h4 className="font-bold text-gray-900 mb-4 text-lg">Product</h4>
              <ul className="space-y-3 text-gray-600">
                <li><Link href="#platforms" className="hover:text-orange-600 transition font-medium">How It Works</Link></li>
                <li><Link href="/login" className="hover:text-orange-600 transition font-medium">Sign In</Link></li>
                <li><Link href="#pricing" className="hover:text-orange-600 transition font-medium">Pricing</Link></li>
                <li><Link href={ctaHref} className="hover:text-orange-600 transition font-medium">Get Started</Link></li>
              </ul>
            </div>
            <div>
              <h4 className="font-bold text-gray-900 mb-4 text-lg">Company</h4>
              <ul className="space-y-3 text-gray-600">
                <li><Link href="/about" className="hover:text-orange-600 transition font-medium">About</Link></li>
                <li><Link href="/privacy" className="hover:text-orange-600 transition font-medium">Privacy</Link></li>
                <li><Link href="/terms" className="hover:text-orange-600 transition font-medium">Terms</Link></li>
              </ul>
            </div>
          </div>
          <div className="pt-8 border-t-2 border-gray-200 text-center">
            <p className="text-gray-600 font-medium">
              © 2026 moreach.ai — Discover leads where conversations happen
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}

// Instagram Content Component
function InstagramContent() {
  return (
    <div className="space-y-12">
      {/* Hero Card */}
      <div className="bg-gradient-to-br from-purple-50 via-pink-50 to-orange-50 rounded-2xl p-8 md:p-12 text-center">
        <h3 className="text-4xl md:text-5xl font-bold text-gray-900 mb-4">
          Find Instagram Creators Your Customers Follow
        </h3>
        <p className="text-lg text-gray-600 mb-8 max-w-2xl mx-auto">
          AI-powered discovery platform that helps you find and connect with Instagram influencers who match your brand perfectly.
        </p>
        <Link
          href="/register"
          className="inline-flex items-center px-8 py-4 bg-gray-900 text-white text-xl font-semibold rounded-xl hover:bg-gray-800 transition shadow-lg hover:shadow-xl transform hover:-translate-y-0.5"
        >
          Sign Up Now
          <svg className="w-5 h-5 ml-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5l7 7-7 7" />
          </svg>
        </Link>
      </div>

      {/* Features Grid */}
      <div className="grid md:grid-cols-3 gap-6">
        <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
          <div className="w-12 h-12 bg-blue-100 rounded-xl flex items-center justify-center mb-4">
            <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          </div>
          <h4 className="text-lg font-bold text-gray-900 mb-2">Intent-Based Search</h4>
          <p className="text-gray-600 text-sm">
            Describe your brand in natural language and let AI find creators that match your vision
          </p>
        </div>

        <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
          <div className="w-12 h-12 bg-purple-100 rounded-xl flex items-center justify-center mb-4">
            <svg className="w-6 h-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
          </div>
          <h4 className="text-lg font-bold text-gray-900 mb-2">Deep Analytics</h4>
          <p className="text-gray-600 text-sm">
            Get comprehensive insights on engagement rates, audience demographics, and more
          </p>
        </div>

        <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
          <div className="w-12 h-12 bg-green-100 rounded-xl flex items-center justify-center mb-4">
            <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
          </div>
          <h4 className="text-lg font-bold text-gray-900 mb-2">Real-Time Data</h4>
          <p className="text-gray-600 text-sm">
            Access up-to-date creator profiles and metrics updated continuously in the background
          </p>
        </div>
      </div>
    </div>
  );
}

// Reddit Content Component
function RedditContent() {
  return (
    <div className="space-y-0">
      {/* Hero Introduction - Bold Orange Section - Full Width */}
      <div className="bg-gradient-to-br from-orange-500 via-orange-600 to-red-600 py-16 md:py-24 text-center relative overflow-hidden">
        {/* Decorative circles */}
        <div className="absolute top-0 right-0 w-64 h-64 bg-white/10 rounded-full -translate-y-1/2 translate-x-1/2"></div>
        <div className="absolute bottom-0 left-0 w-48 h-48 bg-white/10 rounded-full translate-y-1/2 -translate-x-1/2"></div>
        
        <div className="relative z-10 max-w-7xl mx-auto px-6">
          <h3 className="text-4xl md:text-5xl font-bold text-white mb-6 leading-tight">
            Find Leads on Reddit with AI
          </h3>
          <p className="text-xl md:text-2xl text-orange-50 mb-10 max-w-3xl mx-auto leading-relaxed">
            We help you discover and engage with Reddit users interested in your niche using AI.
          </p>

          {/* Demo Video */}
          <div className="max-w-3xl mx-auto mb-12">
            <div className="relative w-full aspect-video rounded-2xl overflow-hidden shadow-2xl">
              <iframe
                src="https://www.youtube.com/embed/yDapAkGtj5Y?si=vvTZvnJVgGmuDRud"
                title="Moreach Demo"
                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
                allowFullScreen
                className="absolute inset-0 w-full h-full"
              />
            </div>
          </div>

          {/* Stats Row */}
          <div className="grid grid-cols-3 gap-4 md:gap-8 max-w-3xl mx-auto mb-16">
            <div className="text-center">
              <div className="text-3xl sm:text-4xl md:text-5xl font-bold text-white mb-2">30%</div>
              <div className="text-sm md:text-base text-orange-100 font-medium">Average Reply Rate</div>
            </div>
            <div className="text-center">
              <div className="text-3xl sm:text-4xl md:text-5xl font-bold text-white mb-2">80%</div>
              <div className="text-sm md:text-base text-orange-100 font-medium">Positive Responses</div>
            </div>
            <div className="text-center">
              <div className="text-3xl sm:text-4xl md:text-5xl font-bold text-white mb-2">100%</div>
              <div className="text-sm md:text-base text-orange-100 font-medium">Users find customers</div>
            </div>
          </div>

        </div>

        <div className="relative z-10">
          <div className="relative overflow-hidden mb-12">
            <div className="flex animate-marquee space-x-6">
              {[
                { quote: "Closed $1,200 MRR from Reddit leads in my first month. The AI finds people actively looking for solutions like mine.", author: "Marcus Chen", role: "Founder", company: "Shipfast.io", avatar: "https://randomuser.me/api/portraits/men/32.jpg" },
                { quote: "3 clients worth $4,500 total came from moreach leads. Saves me 10+ hours/week vs manual Reddit hunting.", author: "Sarah Mitchell", role: "CEO", company: "GrowthLab Agency", avatar: "https://randomuser.me/api/portraits/women/44.jpg" },
                { quote: "15 replies first week, 4 converted to paying users. That's $800/mo recurring from organic Reddit outreach.", author: "Jake Torres", role: "Indie Hacker", company: "LaunchPad Tools", avatar: "https://randomuser.me/api/portraits/men/75.jpg" },
                { quote: "The suggested replies feel genuine. Landed 2 enterprise deals ($3k each) because I showed up at the right moment.", author: "Emily Watson", role: "Marketing Lead", company: "Nexus Commerce", avatar: "https://randomuser.me/api/portraits/women/68.jpg" },
                { quote: "Found 5 perfect-fit leads in subreddits I didn't know existed. Already converted 2 to annual plans worth $600.", author: "David Park", role: "Co-founder", company: "CodeReview.ai", avatar: "https://randomuser.me/api/portraits/men/46.jpg" },
                { quote: "Closed $1,200 MRR from Reddit leads in my first month. The AI finds people actively looking for solutions like mine.", author: "Marcus Chen", role: "Founder", company: "Shipfast.io", avatar: "https://randomuser.me/api/portraits/men/32.jpg" },
                { quote: "3 clients worth $4,500 total came from moreach leads. Saves me 10+ hours/week vs manual Reddit hunting.", author: "Sarah Mitchell", role: "CEO", company: "GrowthLab Agency", avatar: "https://randomuser.me/api/portraits/women/44.jpg" },
                { quote: "15 replies first week, 4 converted to paying users. That's $800/mo recurring from organic Reddit outreach.", author: "Jake Torres", role: "Indie Hacker", company: "LaunchPad Tools", avatar: "https://randomuser.me/api/portraits/men/75.jpg" },
              ].map((story, index) => (
                <div key={index} className="flex-shrink-0 w-96 h-52 bg-white/10 backdrop-blur-sm rounded-2xl p-6 border border-white/20 flex flex-col">
                  <p className="text-white text-base leading-relaxed flex-grow">&ldquo;{story.quote}&rdquo;</p>
                  <div className="flex items-center gap-3 mt-4">
                    <img
                      src={story.avatar}
                      alt={story.author}
                      className="w-10 h-10 rounded-full object-cover border-2 border-white/30"
                    />
                    <div>
                      <div className="text-white font-semibold text-sm">{story.author}</div>
                      <div className="text-orange-200 text-xs">{story.role} @ {story.company}</div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="text-center pb-4">
            <Link
              href="/reddit"
              className="inline-flex items-center px-10 py-5 bg-white text-orange-600 text-lg font-bold rounded-full hover:bg-orange-50 transition-all shadow-2xl hover:shadow-orange-500/50 transform hover:scale-105"
            >
              Start Finding Leads
              <svg className="w-6 h-6 ml-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="3" d="M13 7l5 5m0 0l-5 5m5-5H6" />
              </svg>
            </Link>
          </div>
        </div>
      </div>

      {/* Why Reddit Section - Vibrant Gradient */}
      <div className="bg-gradient-to-br from-amber-100 via-orange-100 to-yellow-100 py-16 md:py-24 relative overflow-hidden">
        {/* Decorative Elements */}
        <div className="absolute top-20 left-10 w-32 h-32 bg-orange-300/30 rounded-full blur-3xl"></div>
        <div className="absolute bottom-20 right-10 w-40 h-40 bg-yellow-300/30 rounded-full blur-3xl"></div>

        <div className="max-w-7xl mx-auto px-6 relative z-10">
          {/* Header */}
          <div className="text-center mb-16">
            <h3 className="text-4xl md:text-5xl font-bold text-gray-900 mb-4 leading-tight">
              Your potential audience are already on <span className="bg-gradient-to-r from-orange-500 to-red-500 bg-clip-text text-transparent">Reddit</span>
            </h3>
            <p className="text-lg text-gray-600 max-w-3xl mx-auto leading-relaxed">
              Connect with <span className="text-2xl font-bold text-orange-500">100M+</span> daily active users in <span className="text-2xl font-bold text-orange-500">100K+</span> niche communities who are actively discussing the exact problems you solve.
            </p>
          </div>

          {/* Two Cards Side by Side */}
          <div className="grid lg:grid-cols-2 gap-6">
            {/* Left Card - Real Conversations */}
            <div className="bg-gradient-to-br from-orange-500 to-red-500 rounded-3xl p-8 md:p-10 text-white relative overflow-hidden group hover:shadow-2xl transition-all duration-300">
              <div className="absolute top-0 right-0 w-48 h-48 bg-white/10 rounded-full -translate-y-1/2 translate-x-1/2 group-hover:scale-150 transition-transform duration-500"></div>
              <div className="relative z-10">
                <div className="w-16 h-16 bg-white/20 backdrop-blur rounded-2xl flex items-center justify-center mb-6">
                  <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17 8h2a2 2 0 012 2v6a2 2 0 01-2 2h-2v4l-4-4H9a1.994 1.994 0 01-1.414-.586m0 0L11 14h4a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2v4l.586-.586z" />
                  </svg>
                </div>
                <h4 className="text-xl md:text-2xl font-semibold mb-4">Real conversations, real intent</h4>
                <p className="text-orange-100 text-lg leading-relaxed">
                  People on Reddit ask for recommendations, share problems, and seek solutions. They're not just browsing—they're actively looking for products like yours.
                </p>
              </div>
            </div>

            {/* Right Card - Influence AI */}
            <div className="bg-white rounded-3xl p-8 md:p-10 shadow-xl hover:shadow-2xl transition-all duration-300 border-2 border-orange-100 group">
              <div className="w-16 h-16 bg-gradient-to-br from-purple-500 to-indigo-500 rounded-2xl flex items-center justify-center mb-6 group-hover:scale-110 group-hover:rotate-3 transition-all">
                <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                </svg>
              </div>
              <h4 className="text-2xl md:text-2xl md:text-3xl font-bold text-gray-900 mb-4">Influence AI recommendations</h4>
              <p className="text-gray-600 text-lg leading-relaxed mb-6">
                Reddit content is used to train LLMs. Being active there means shaping how AI recommends products in the future.
              </p>
              {/* LLM Icons */}
              <div className="flex items-center gap-4">
                <span className="text-sm text-gray-500 font-medium">Powering:</span>
                <div className="flex items-center gap-3">
                  {/* OpenAI/GPT */}
                  <div className="w-10 h-10 bg-gray-900 rounded-xl flex items-center justify-center" title="OpenAI GPT">
                    <svg className="w-6 h-6 text-white" viewBox="0 0 24 24" fill="currentColor">
                      <path d="M22.2819 9.8211a5.9847 5.9847 0 0 0-.5157-4.9108 6.0462 6.0462 0 0 0-6.5098-2.9A6.0651 6.0651 0 0 0 4.9807 4.1818a5.9847 5.9847 0 0 0-3.9977 2.9 6.0462 6.0462 0 0 0 .7427 7.0966 5.98 5.98 0 0 0 .511 4.9107 6.051 6.051 0 0 0 6.5146 2.9001A5.9847 5.9847 0 0 0 13.2599 24a6.0557 6.0557 0 0 0 5.7718-4.2058 5.9894 5.9894 0 0 0 3.9977-2.9001 6.0557 6.0557 0 0 0-.7475-7.0729zm-9.022 12.6081a4.4755 4.4755 0 0 1-2.8764-1.0408l.1419-.0804 4.7783-2.7582a.7948.7948 0 0 0 .3927-.6813v-6.7369l2.02 1.1686a.071.071 0 0 1 .038.052v5.5826a4.504 4.504 0 0 1-4.4945 4.4944zm-9.6607-4.1254a4.4708 4.4708 0 0 1-.5346-3.0137l.142.0852 4.783 2.7582a.7712.7712 0 0 0 .7806 0l5.8428-3.3685v2.3324a.0804.0804 0 0 1-.0332.0615L9.74 19.9502a4.4992 4.4992 0 0 1-6.1408-1.6464zM2.3408 7.8956a4.485 4.485 0 0 1 2.3655-1.9728V11.6a.7664.7664 0 0 0 .3879.6765l5.8144 3.3543-2.0201 1.1685a.0757.0757 0 0 1-.071 0l-4.8303-2.7865A4.504 4.504 0 0 1 2.3408 7.8956zm16.5963 3.8558L13.1038 8.364 15.1192 7.2a.0757.0757 0 0 1 .071 0l4.8303 2.7913a4.4944 4.4944 0 0 1-.6765 8.1042v-5.6772a.79.79 0 0 0-.407-.667zm2.0107-3.0231l-.142-.0852-4.7735-2.7818a.7759.7759 0 0 0-.7854 0L9.409 9.2297V6.8974a.0662.0662 0 0 1 .0284-.0615l4.8303-2.7866a4.4992 4.4992 0 0 1 6.6802 4.66zM8.3065 12.863l-2.02-1.1638a.0804.0804 0 0 1-.038-.0567V6.0742a4.4992 4.4992 0 0 1 7.3757-3.4537l-.142.0805L8.704 5.459a.7948.7948 0 0 0-.3927.6813zm1.0976-2.3654l2.602-1.4998 2.6069 1.4998v2.9994l-2.5974 1.4997-2.6067-1.4997Z"/>
                    </svg>
                  </div>
                  {/* Google Gemini - Star shape */}
                  <div className="w-10 h-10 bg-white rounded-xl flex items-center justify-center border border-gray-200" title="Google Gemini">
                    <svg className="w-6 h-6" viewBox="0 0 28 28" fill="none">
                      <path d="M14 0C14 7.732 7.732 14 0 14c7.732 0 14 6.268 14 14 0-7.732 6.268-14 14-14-7.732 0-14-6.268-14-14Z" fill="url(#gemini-gradient)"/>
                      <defs>
                        <linearGradient id="gemini-gradient" x1="0" y1="0" x2="28" y2="28" gradientUnits="userSpaceOnUse">
                          <stop stopColor="#1A73E8"/>
                          <stop offset="0.5" stopColor="#6C47FF"/>
                          <stop offset="1" stopColor="#F02A4D"/>
                        </linearGradient>
                      </defs>
                    </svg>
                  </div>
                  {/* Anthropic Claude */}
                  <div className="w-10 h-10 rounded-xl flex items-center justify-center overflow-hidden" title="Anthropic Claude">
                    <svg className="w-10 h-10" viewBox="0 0 512 509.64">
                      <path fill="#D77655" d="M115.612 0h280.775C459.974 0 512 52.026 512 115.612v278.415c0 63.587-52.026 115.612-115.613 115.612H115.612C52.026 509.639 0 457.614 0 394.027V115.612C0 52.026 52.026 0 115.612 0z"/>
                      <path fill="#FCF2EE" fillRule="nonzero" d="M142.27 316.619l73.655-41.326 1.238-3.589-1.238-1.996-3.589-.001-12.31-.759-42.084-1.138-36.498-1.516-35.361-1.896-8.897-1.895-8.34-10.995.859-5.484 7.482-5.03 10.717.935 23.683 1.617 35.537 2.452 25.782 1.517 38.193 3.968h6.064l.86-2.451-2.073-1.517-1.618-1.517-36.776-24.922-39.81-26.338-20.852-15.166-11.273-7.683-5.687-7.204-2.451-15.721 10.237-11.273 13.75.935 3.513.936 13.928 10.716 29.749 23.027 38.848 28.612 5.687 4.727 2.275-1.617.278-1.138-2.553-4.271-21.13-38.193-22.546-38.848-10.035-16.101-2.654-9.655c-.935-3.968-1.617-7.304-1.617-11.374l11.652-15.823 6.445-2.073 15.545 2.073 6.547 5.687 9.655 22.092 15.646 34.78 24.265 47.291 7.103 14.028 3.791 12.992 1.416 3.968 2.449-.001v-2.275l1.997-26.641 3.69-32.707 3.589-42.084 1.239-11.854 5.863-14.206 11.652-7.683 9.099 4.348 7.482 10.716-1.036 6.926-4.449 28.915-8.72 45.294-5.687 30.331h3.313l3.792-3.791 15.342-20.372 25.782-32.227 11.374-12.789 13.27-14.129 8.517-6.724 16.1-.001 11.854 17.617-5.307 18.199-16.581 21.029-13.75 17.819-19.716 26.54-12.309 21.231 1.138 1.694 2.932-.278 44.536-9.479 24.062-4.347 28.714-4.928 12.992 6.066 1.416 6.167-5.106 12.613-30.71 7.583-36.018 7.204-53.636 12.689-.657.48.758.935 24.164 2.275 10.337.556h25.301l47.114 3.514 12.309 8.139 7.381 9.959-1.238 7.583-18.957 9.655-25.579-6.066-59.702-14.205-20.474-5.106-2.83-.001v1.694l17.061 16.682 31.266 28.233 39.152 36.397 1.997 8.999-5.03 7.102-5.307-.758-34.401-25.883-13.27-11.651-30.053-25.302-1.996-.001v2.654l6.926 10.136 36.574 54.975 1.895 16.859-2.653 5.485-9.479 3.311-10.414-1.895-21.408-30.054-22.092-33.844-17.819-30.331-2.173 1.238-10.515 113.261-4.929 5.788-11.374 4.348-9.478-7.204-5.03-11.652 5.03-23.027 6.066-30.052 4.928-23.886 4.449-29.674 2.654-9.858-.177-.657-2.173.278-22.37 30.71-34.021 45.977-26.919 28.815-6.445 2.553-11.173-5.789 1.037-10.337 6.243-9.2 37.257-47.392 22.47-29.371 14.508-16.961-.101-2.451h-.859l-98.954 64.251-17.618 2.275-7.583-7.103.936-11.652 3.589-3.791 29.749-20.474z"/>
                    </svg>
                  </div>
                  {/* xAI Grok */}
                  <div className="w-10 h-10 rounded-xl flex items-center justify-center overflow-hidden" title="xAI Grok">
                    <svg className="w-10 h-10" viewBox="0 0 512 509.641">
                      <path d="M115.612 0h280.776C459.975 0 512 52.026 512 115.612v278.416c0 63.587-52.025 115.613-115.612 115.613H115.612C52.026 509.641 0 457.615 0 394.028V115.612C0 52.026 52.026 0 115.612 0z"/>
                      <path fill="#fff" d="M213.235 306.019l178.976-180.002v.169l51.695-51.763c-.924 1.32-1.86 2.605-2.785 3.89-39.281 54.164-58.46 80.649-43.07 146.922l-.09-.101c10.61 45.11-.744 95.137-37.398 131.836-46.216 46.306-120.167 56.611-181.063 14.928l42.462-19.675c38.863 15.278 81.392 8.57 111.947-22.03 30.566-30.6 37.432-75.159 22.065-112.252-2.92-7.025-11.67-8.795-17.792-4.263l-124.947 92.341zm-25.786 22.437l-.033.034L68.094 435.217c7.565-10.429 16.957-20.294 26.327-30.149 26.428-27.803 52.653-55.359 36.654-94.302-21.422-52.112-8.952-113.177 30.724-152.898 41.243-41.254 101.98-51.661 152.706-30.758 11.23 4.172 21.016 10.114 28.638 15.639l-42.359 19.584c-39.44-16.563-84.629-5.299-112.207 22.313-37.298 37.308-44.84 102.003-1.128 143.81z"/>
                    </svg>
                  </div>
                  {/* Ellipsis for more */}
                  <span className="text-gray-400 font-bold text-xl ml-1">...</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* The Challenge Section - Dark Contrasting */}
      <div className="bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 py-16 md:py-24 relative overflow-hidden">
        {/* Decorative grid pattern */}
        <div className="absolute inset-0 opacity-5">
          <div className="absolute inset-0" style={{ backgroundImage: 'radial-gradient(circle at 1px 1px, white 1px, transparent 0)', backgroundSize: '40px 40px' }}></div>
        </div>

        <div className="max-w-7xl mx-auto px-6 relative z-10">
          {/* Header */}
          <div className="text-center mb-16">
            <h3 className="text-4xl md:text-5xl font-bold text-white mb-6 leading-tight">
              But it's <span className="bg-gradient-to-r from-red-400 to-orange-400 bg-clip-text text-transparent">tricky</span> to get right
            </h3>
            <p className="text-base md:text-lg text-gray-400 max-w-2xl mx-auto">
              Reddit users are smart. They can smell marketing from a mile away.
            </p>
          </div>

          {/* Horizontal Scrolling Cards on Mobile, Grid on Desktop */}
          <div className="grid md:grid-cols-3 gap-6">
            <div className="bg-white/5 backdrop-blur border border-white/10 rounded-3xl p-8 hover:bg-white/10 transition-all group">
              <div className="w-12 h-12 bg-blue-500/20 rounded-xl flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
                <svg className="w-6 h-6 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
              </div>
              <h4 className="text-xl font-semibold text-white mb-3">Finding the right subreddits</h4>
              <p className="text-gray-400 leading-relaxed">
                Thousands of communities exist. Finding the ones where your audience actually hangs out takes serious research.
              </p>
            </div>

            <div className="bg-white/5 backdrop-blur border border-white/10 rounded-3xl p-8 hover:bg-white/10 transition-all group">
              <div className="w-12 h-12 bg-yellow-500/20 rounded-xl flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
                <svg className="w-6 h-6 text-yellow-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <h4 className="text-xl font-semibold text-white mb-3">Timing matters</h4>
              <p className="text-gray-400 leading-relaxed">
                Miss the window and the conversation moves on. You need to catch relevant posts when they're fresh.
              </p>
            </div>

            <div className="bg-white/5 backdrop-blur border border-white/10 rounded-3xl p-8 hover:bg-white/10 transition-all group">
              <div className="w-12 h-12 bg-red-500/20 rounded-xl flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
                <svg className="w-6 h-6 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
              </div>
              <h4 className="text-xl font-semibold text-white mb-3">Staying authentic & safe</h4>
              <p className="text-gray-400 leading-relaxed">
                Generic responses get downvoted. Self-promote wrong and you're banned. You need genuine replies that help.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Feature 1: Discover Subreddits - Cream/Beige Section - Full Width */}
      <div className="bg-gradient-to-br from-amber-50 via-orange-50 to-yellow-50 py-16 md:py-24">
        {/* Section Header */}
        <div className="text-center mb-16">
          <h2 className="text-4xl md:text-5xl font-bold text-gray-900">How Moreach works</h2>
        </div>
        <div className="max-w-7xl mx-auto px-6 grid md:grid-cols-2 gap-12 items-center">
            <div>
            <div className="inline-block px-5 py-2 bg-orange-500 text-white rounded-full text-sm font-bold mb-6 shadow-lg">
              STEP 1
            </div>
            <h3 className="text-4xl md:text-5xl font-bold text-gray-900 mb-6 leading-tight">
              Discover relevant subreddits
            </h3>
            <p className="text-lg text-gray-600 mb-8 leading-relaxed">
              Tell us about your business and target audience. Our AI analyzes millions of subreddits to find communities where your potential customers hang out.
            </p>
            <ul className="space-y-4">
              {[
                "AI-powered subreddit discovery",
                "Community activity analysis",
                "Audience demographic matching",
                "Relevance scoring and ranking"
              ].map((feature, index) => (
                <li key={index} className="flex items-center gap-3 text-gray-800">
                  <div className="w-7 h-7 bg-orange-500 rounded-full flex items-center justify-center flex-shrink-0">
                    <svg className="w-4 h-4 text-white" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                    </svg>
                  </div>
                  <span className="text-lg font-medium">{feature}</span>
                </li>
              ))}
              </ul>
            </div>
          <div className="bg-white rounded-3xl p-8 shadow-2xl border-4 border-orange-200">
            <div className="text-sm font-semibold text-gray-500 mb-3 uppercase tracking-wide">Business Description</div>
            <div className="text-gray-900 mb-6 text-base">
              "We build productivity tools for remote teams..."
          </div>
            <div className="text-sm font-semibold text-gray-500 mb-3 uppercase tracking-wide">Discovered Subreddits</div>
            <div className="flex flex-wrap gap-3 mb-6">
              <span className="px-4 py-2 bg-gradient-to-r from-orange-400 to-red-400 text-white rounded-full text-sm font-bold shadow-lg">
                r/productivity
              </span>
              <span className="px-4 py-2 bg-gradient-to-r from-orange-400 to-red-400 text-white rounded-full text-sm font-bold shadow-lg">
                r/startups
              </span>
              <span className="px-4 py-2 bg-gradient-to-r from-orange-400 to-red-400 text-white rounded-full text-sm font-bold shadow-lg">
                r/remotework
              </span>
            </div>
            <button className="w-full bg-gradient-to-r from-orange-500 to-red-500 text-white py-4 rounded-full font-bold text-lg hover:from-orange-600 hover:to-red-600 transition-all shadow-xl hover:shadow-2xl transform hover:scale-105">
              Discover Communities
            </button>
          </div>
        </div>
      </div>

      {/* Feature 2: Track Relevant Posts - Deep Red/Maroon Section - Full Width */}
      <div className="bg-gradient-to-br from-red-900 via-red-800 to-orange-900 py-16 md:py-24 relative overflow-hidden">
        {/* Decorative elements */}
        <div className="absolute top-0 left-0 w-96 h-96 bg-orange-500/20 rounded-full -translate-x-1/2 -translate-y-1/2"></div>
        <div className="absolute bottom-0 right-0 w-80 h-80 bg-red-500/20 rounded-full translate-x-1/3 translate-y-1/3"></div>
        
        <div className="max-w-7xl mx-auto px-6 grid md:grid-cols-2 gap-12 items-center relative z-10">
          <div className="order-2 md:order-1">
            <div className="space-y-4">
              <div className="bg-white/95 backdrop-blur rounded-2xl p-6 shadow-2xl transform hover:scale-105 transition-transform">
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <span className="text-base font-bold text-gray-900">u/startup_founder</span>
                    <span className="text-xs text-gray-500">2h ago</span>
                  </div>
                  <span className="px-3 py-1 bg-green-500 text-white text-xs font-bold rounded-full">100% match</span>
                </div>
                <p className="text-gray-800 mb-3 leading-relaxed">
                  "Looking for a better way to manage my remote team's tasks..."
                </p>
                <div className="flex items-center gap-3 text-xs text-gray-600 font-medium">
                  <span className="px-2 py-1 bg-orange-100 rounded">r/startups</span>
                  <span>•</span>
                  <span>12 comments</span>
                </div>
              </div>
              <div className="bg-white/95 backdrop-blur rounded-2xl p-6 shadow-2xl transform hover:scale-105 transition-transform">
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <span className="text-base font-bold text-gray-900">u/remote_manager</span>
                    <span className="text-xs text-gray-500">5h ago</span>
                  </div>
                  <span className="px-3 py-1 bg-yellow-500 text-white text-xs font-bold rounded-full">90% match</span>
                </div>
                <p className="text-gray-800 mb-3 leading-relaxed">
                  "Any recommendations for productivity apps that work well for distributed teams?"
                </p>
                <div className="flex items-center gap-3 text-xs text-gray-600 font-medium">
                  <span className="px-2 py-1 bg-orange-100 rounded">r/remotework</span>
                  <span>•</span>
                  <span>8 comments</span>
                </div>
              </div>
            </div>
          </div>
          <div className="order-1 md:order-2">
            <div className="inline-block px-5 py-2 bg-white text-red-900 rounded-full text-sm font-bold mb-6 shadow-lg">
              STEP 2
            </div>
            <h3 className="text-4xl md:text-5xl font-bold text-white mb-6 leading-tight">
              Track relevant posts in real-time
            </h3>
            <p className="text-xl text-red-50 mb-8 leading-relaxed">
              Our AI continuously monitors your selected subreddits and identifies posts from users who are actively looking for solutions like yours.
            </p>
            <ul className="space-y-4">
              {[
                "Real-time post monitoring",
                "AI-powered relevance scoring",
                "User intent analysis",
                "Conversation context understanding"
              ].map((feature, index) => (
                <li key={index} className="flex items-center gap-3 text-white">
                  <div className="w-7 h-7 bg-white rounded-full flex items-center justify-center flex-shrink-0">
                    <svg className="w-4 h-4 text-red-900" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
                  </div>
                  <span className="text-lg font-medium">{feature}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>

      {/* Feature 3: Auto-generate Comments & DMs - Light Green/Yellow Section - Full Width */}
      <div className="bg-gradient-to-br from-lime-100 via-yellow-100 to-green-100 py-16 md:py-24">
        <div className="max-w-7xl mx-auto px-6 grid md:grid-cols-2 gap-12 items-center">
          <div>
            <div className="inline-block px-5 py-2 bg-green-600 text-white rounded-full text-sm font-bold mb-6 shadow-lg">
              STEP 3
            </div>
            <h3 className="text-4xl md:text-5xl font-bold text-gray-900 mb-6 leading-tight">
              Auto-generate comments and DMs
            </h3>
            <p className="text-lg text-gray-600 mb-8 leading-relaxed">
              Generate authentic, personalized comments and direct messages for each post. Our AI understands context and writes responses that sound human and drive real engagement.
            </p>
            <ul className="space-y-4">
              {[
                "Context-aware response generation",
                "Personalized comment suggestions",
                "DM templates with customization",
                "Authentic tone and style matching"
              ].map((feature, index) => (
                <li key={index} className="flex items-center gap-3 text-gray-800">
                  <div className="w-7 h-7 bg-green-600 rounded-full flex items-center justify-center flex-shrink-0">
                    <svg className="w-4 h-4 text-white" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
                  </div>
                  <span className="text-lg font-medium">{feature}</span>
                </li>
              ))}
            </ul>
          </div>
          <div className="bg-white rounded-3xl p-8 shadow-2xl border-4 border-green-200">
            <div className="flex items-center justify-between mb-6">
              <span className="font-bold text-xl text-gray-900">Suggested Comment</span>
              <span className="px-4 py-2 bg-gradient-to-r from-green-500 to-emerald-500 text-white rounded-full text-sm font-bold shadow-lg">
                READY
              </span>
            </div>
            <div className="bg-gradient-to-br from-green-50 to-lime-50 rounded-2xl p-6 mb-6 border-2 border-green-200">
              <p className="text-gray-800 leading-relaxed text-lg">
                "Hey! I've been using a tool that sounds perfect for your situation. It's designed specifically for remote teams and has really helped us stay organized. Happy to share more details if you're interested!"
              </p>
            </div>
            <div className="flex gap-3">
              <button className="flex-1 px-6 py-4 bg-gradient-to-r from-green-500 to-emerald-500 text-white rounded-full font-bold hover:from-green-600 hover:to-emerald-600 transition-all shadow-xl hover:shadow-2xl transform hover:scale-105">
                Copy Response
              </button>
              <button className="px-6 py-4 border-3 border-green-600 text-green-700 rounded-full font-bold hover:bg-green-50 transition-all">
                Regenerate
              </button>
            </div>
          </div>
        </div>
      </div>

    </div>
  );
}

// Coming Soon Content Component
function ComingSoonContent({ platform }: { platform: string }) {
  return (
    <div className="bg-gradient-to-br from-gray-50 to-gray-100 rounded-2xl p-12 md:p-16 text-center">
      <div className="max-w-2xl mx-auto">
        <div className="w-20 h-20 bg-gray-200 rounded-full flex items-center justify-center mx-auto mb-6">
          <svg className="w-10 h-10 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                </svg>
            </div>
        <h3 className="text-4xl md:text-5xl font-bold text-gray-900 mb-4">
          {platform} Support Coming Soon
        </h3>
        <p className="text-lg text-gray-600 mb-8">
          We're working hard to bring {platform} influencer discovery to moreach.ai. 
          Stay tuned for updates!
        </p>
        <div className="inline-flex items-center px-6 py-3 bg-white rounded-xl text-gray-700 border-2 border-gray-300">
          <svg className="w-5 h-5 mr-2 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <span className="font-semibold">In Development</span>
          </div>
        </div>
    </div>
  );
}
