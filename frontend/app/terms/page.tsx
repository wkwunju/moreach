"use client";

import Navigation from "../../components/Navigation";

export default function TermsPage() {
  return (
    <div className="min-h-screen bg-white">
      <Navigation />

      <div className="max-w-4xl mx-auto px-6 pt-32 pb-20">
        <h1 className="text-5xl md:text-6xl font-black text-gray-900 mb-6">
          Terms of Service
        </h1>
        <p className="text-lg text-gray-600 mb-12">
          Last updated: January 24, 2026
        </p>

        <div className="prose prose-lg max-w-none space-y-8">
          {/* 1. Acceptance of Terms */}
          <section>
            <h2 className="text-2xl font-bold text-gray-900 mb-4">1. Acceptance of Terms</h2>
            <p className="text-gray-700 leading-relaxed">
              By accessing or using Moreach's services, you agree to be bound by these Terms of Service. If you do not agree to these terms, please do not use our platform.
            </p>
          </section>

          {/* 2. Description of Service */}
          <section>
            <h2 className="text-2xl font-bold text-gray-900 mb-4">2. Description of Service</h2>
            <p className="text-gray-700 leading-relaxed">
              Moreach provides AI-powered audience discovery and influencer matching services. We help businesses identify and connect with relevant audiences, communities, and influencers across various online platforms including Reddit, Instagram, Twitter, and TikTok.
            </p>
          </section>

          {/* 3. User Accounts */}
          <section>
            <h2 className="text-2xl font-bold text-gray-900 mb-4">3. User Accounts</h2>
            <p className="text-gray-700 leading-relaxed mb-3">
              You are responsible for maintaining the confidentiality of your account credentials and for all activities that occur under your account. You agree to:
            </p>
            <ul className="list-disc list-inside text-gray-700 space-y-2 ml-4">
              <li>Provide accurate and complete information during registration</li>
              <li>Keep your account information up to date</li>
              <li>Notify us immediately of any unauthorized use of your account</li>
              <li>Use the service in compliance with all applicable laws and regulations</li>
            </ul>
          </section>

          {/* 4. Acceptable Use */}
          <section>
            <h2 className="text-2xl font-bold text-gray-900 mb-4">4. Acceptable Use</h2>
            <p className="text-gray-700 leading-relaxed mb-3">
              You agree not to use Moreach to:
            </p>
            <ul className="list-disc list-inside text-gray-700 space-y-2 ml-4">
              <li>Spam or harass users on any platform</li>
              <li>Violate any platform's terms of service or community guidelines</li>
              <li>Engage in fraudulent or deceptive practices</li>
              <li>Collect or store personal data without proper consent</li>
              <li>Use automated tools to scrape or abuse our service</li>
            </ul>
          </section>

          {/* 5. Intellectual Property */}
          <section>
            <h2 className="text-2xl font-bold text-gray-900 mb-4">5. Intellectual Property</h2>
            <p className="text-gray-700 leading-relaxed">
              All content, features, and functionality of Moreach, including but not limited to text, graphics, logos, and software, are owned by Moreach and protected by international copyright and trademark laws.
            </p>
          </section>

          {/* 6. Payment and Subscription */}
          <section>
            <h2 className="text-2xl font-bold text-gray-900 mb-4">6. Payment and Subscription</h2>
            <p className="text-gray-700 leading-relaxed">
              Subscription fees are billed in advance on a recurring basis. You may cancel your subscription at any time, but refunds are not provided for partial subscription periods. We offer a 14-day free trial with no credit card required.
            </p>
          </section>

          {/* 7. Limitation of Liability */}
          <section>
            <h2 className="text-2xl font-bold text-gray-900 mb-4">7. Limitation of Liability</h2>
            <p className="text-gray-700 leading-relaxed">
              Moreach is provided "as is" without warranties of any kind. We are not liable for any indirect, incidental, or consequential damages arising from your use of the service. Our total liability shall not exceed the amount you paid for the service in the past 12 months.
            </p>
          </section>

          {/* 8. Termination */}
          <section>
            <h2 className="text-2xl font-bold text-gray-900 mb-4">8. Termination</h2>
            <p className="text-gray-700 leading-relaxed">
              We reserve the right to suspend or terminate your account at any time for violation of these terms or for any other reason at our sole discretion. Upon termination, your right to use the service will immediately cease.
            </p>
          </section>

          {/* 9. Changes to Terms */}
          <section>
            <h2 className="text-2xl font-bold text-gray-900 mb-4">9. Changes to Terms</h2>
            <p className="text-gray-700 leading-relaxed">
              We may update these Terms of Service from time to time. We will notify users of any material changes via email or through the platform. Continued use of the service after changes constitutes acceptance of the updated terms.
            </p>
          </section>

          {/* Contact */}
          <section>
            <h2 className="text-2xl font-bold text-gray-900 mb-4">Contact Information</h2>
            <p className="text-gray-700 leading-relaxed mb-4">
              If you have any questions about these Terms of Service, please contact us at:
            </p>
            <p className="text-gray-900">
              <strong>Email:</strong>{" "}
              <a href="mailto:info@moreach.ai" className="text-blue-600 hover:underline font-semibold">
                info@moreach.ai
              </a>
            </p>
          </section>
        </div>
      </div>

      {/* Footer */}
      <footer className="py-16 px-6 bg-gradient-to-br from-gray-50 to-purple-50">
        <div className="max-w-7xl mx-auto">
          <div className="grid md:grid-cols-4 gap-12 mb-12">
            <div className="md:col-span-2">
              <div className="text-4xl font-black bg-gradient-to-r from-orange-600 to-purple-600 bg-clip-text text-transparent mb-6">
                moreach.ai
              </div>
              <p className="text-gray-700 text-lg mb-6 leading-relaxed">
                AI-powered influencer discovery for modern brands. Find leads on Reddit with intelligent automation.
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
                    <path d="M12 0A12 12 0 0 0 0 12a12 12 0 0 0 12 12 12 12 0 0 0 12-12A12 12 0 0 0 12 0zm5.01 4.744c.688 0 1.25.561 1.25 1.249a1.25 1.25 0 0 1-2.498.056l-2.597-.547-.8 3.747c1.824.07 3.48.632 4.674 1.488.308-.309.73-.491 1.207-.491.968 0 1.754.786 1.754 1.754 0 .716-.435 1.333-1.01 1.614a3.111 3.111 0 0 1 .042.52c0 2.694-3.13 4.87-7.004 4.87-3.874 0-7.004-2.176-7.004-4.87 0-.183.015-.366.043-.534A1.748 1.748 0 0 1 4.028 12c0-.968.786-1.754 1.754-1.754.463 0 .898.196 1.207.49 1.207-.883 2.878-1.43 4.744-1.487l.885-4.182a.342.342 0 0 1 .14-.197.35.35 0 0 1 .238-.042l2.906.617a1.214 1.214 0 0 1 1.108-.701zM9.25 12C8.561 12 8 12.562 8 13.25c0 .687.561 1.248 1.25 1.248.687 0 1.248-.561 1.248-1.249 0-.688-.561-1.249-1.249-1.249zm5.5 0c-.687 0-1.248.561-1.248 1.25 0 .687.561 1.248 1.249 1.248.688 0 1.249-.561 1.249-1.249 0-.687-.562-1.249-1.25-1.249z"/>
                  </svg>
                </a>
              </div>
            </div>
            <div>
              <h4 className="font-bold text-gray-900 mb-4 text-lg">Product</h4>
              <ul className="space-y-3 text-gray-600">
                <li><Link href="/#features" className="hover:text-orange-600 transition font-medium">Features</Link></li>
                <li><Link href="/#use-cases" className="hover:text-orange-600 transition font-medium">Use Cases</Link></li>
                <li><Link href="/demo" className="hover:text-orange-600 transition font-medium">Request Demo</Link></li>
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
              © 2026 moreach.ai — Connecting brands with the right creators 🚀
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}

