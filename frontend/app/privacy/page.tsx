"use client";

import Navigation from "../../components/Navigation";

export default function PrivacyPage() {
  return (
    <div className="min-h-screen bg-white">
      <Navigation />

      <div className="max-w-4xl mx-auto px-6 pt-32 pb-20">
        <h1 className="text-5xl md:text-6xl font-black text-gray-900 mb-6">
          Privacy Policy
        </h1>
        <p className="text-lg text-gray-600 mb-12">
          Last updated: January 24, 2026
        </p>

        <div className="prose prose-lg max-w-none space-y-8">
          {/* Introduction */}
          <section>
            <p className="text-gray-700 leading-relaxed">
              At Moreach, we take your privacy seriously. This Privacy Policy explains how we collect, use, and protect your personal information when you use our platform.
            </p>
          </section>

          {/* 1. Data Ownership */}
          <section>
            <h2 className="text-2xl font-bold text-gray-900 mb-4">1. Your Data Belongs to You</h2>
            <p className="text-gray-700 leading-relaxed">
              <strong>All data you create, upload, or generate through Moreach remains your property.</strong> We act only as a processor of your data and will never claim ownership of your campaigns, discoveries, or insights. You maintain full control and can export or delete your data at any time.
            </p>
          </section>

          {/* 2. Information We Collect */}
          <section>
            <h2 className="text-2xl font-bold text-gray-900 mb-4">2. Information We Collect</h2>
            <p className="text-gray-700 leading-relaxed mb-3">
              We collect information that you provide directly to us:
            </p>
            <ul className="list-disc list-inside text-gray-700 space-y-2 ml-4">
              <li>Account information (name, email address, password)</li>
              <li>Business information and campaign details</li>
              <li>Search queries and discovery preferences</li>
              <li>Usage data and analytics</li>
              <li>Communication preferences</li>
            </ul>
          </section>

          {/* 3. How We Use Your Information */}
          <section>
            <h2 className="text-2xl font-bold text-gray-900 mb-4">3. How We Use Your Information</h2>
            <p className="text-gray-700 leading-relaxed mb-3">
              We use the information we collect to:
            </p>
            <ul className="list-disc list-inside text-gray-700 space-y-2 ml-4">
              <li>Provide and improve our audience discovery services</li>
              <li>Process your searches and generate insights</li>
              <li>Send you service updates and important notifications</li>
              <li>Analyze usage patterns to improve our platform</li>
              <li>Provide customer support</li>
            </ul>
          </section>

          {/* 4. Data Sharing */}
          <section>
            <h2 className="text-2xl font-bold text-gray-900 mb-4">4. We Never Share Your Data</h2>
            <p className="text-gray-700 leading-relaxed mb-3">
              <strong>Your data is never sold, rented, or shared with third parties.</strong> We do not:
            </p>
            <ul className="list-disc list-inside text-gray-700 space-y-2 ml-4">
              <li>Sell your personal information to advertisers or data brokers</li>
              <li>Share your campaign data with competitors</li>
              <li>Use your data to train AI models for other customers</li>
              <li>Provide your information to third-party marketing services</li>
            </ul>
            <p className="text-gray-700 leading-relaxed mt-3">
              The only exception is when required by law or to protect our legal rights, and we will notify you whenever legally possible.
            </p>
          </section>

          {/* 5. Data Security */}
          <section>
            <h2 className="text-2xl font-bold text-gray-900 mb-4">5. Data Security</h2>
            <p className="text-gray-700 leading-relaxed">
              We implement industry-standard security measures to protect your data, including encryption, secure data storage, regular security audits, and access controls. However, no method of transmission over the Internet is 100% secure, and we cannot guarantee absolute security.
            </p>
          </section>

          {/* 6. GDPR Compliance */}
          <section>
            <h2 className="text-2xl font-bold text-gray-900 mb-4">6. GDPR Compliance</h2>
            <p className="text-gray-700 leading-relaxed mb-3">
              <strong>We fully comply with the General Data Protection Regulation (GDPR)</strong> and respect your rights as a data subject. You have the right to:
            </p>
            <ul className="list-disc list-inside text-gray-700 space-y-2 ml-4">
              <li><strong>Access:</strong> Request a copy of your personal data</li>
              <li><strong>Rectification:</strong> Correct inaccurate or incomplete data</li>
              <li><strong>Erasure:</strong> Request deletion of your personal data</li>
              <li><strong>Portability:</strong> Export your data in a machine-readable format</li>
              <li><strong>Restriction:</strong> Limit how we process your data</li>
              <li><strong>Objection:</strong> Object to certain types of data processing</li>
            </ul>
            <p className="text-gray-700 leading-relaxed mt-3">
              To exercise any of these rights, contact us at{" "}
              <a href="mailto:privacy@moreach.ai" className="text-blue-600 hover:underline">
                privacy@moreach.ai
              </a>
            </p>
          </section>

          {/* 7. Data Retention */}
          <section>
            <h2 className="text-2xl font-bold text-gray-900 mb-4">7. Data Retention</h2>
            <p className="text-gray-700 leading-relaxed">
              We retain your data only as long as necessary to provide our services and comply with legal obligations. When you delete your account, we will permanently delete your personal data within 30 days, except where we are required by law to retain certain information.
            </p>
          </section>

          {/* 8. Cookies */}
          <section>
            <h2 className="text-2xl font-bold text-gray-900 mb-4">8. Cookies and Tracking</h2>
            <p className="text-gray-700 leading-relaxed">
              We use essential cookies to maintain your session and preferences. We do not use third-party tracking cookies or sell your browsing data to advertisers. You can control cookie settings through your browser.
            </p>
          </section>

          {/* 9. International Data Transfers */}
          <section>
            <h2 className="text-2xl font-bold text-gray-900 mb-4">9. International Data Transfers</h2>
            <p className="text-gray-700 leading-relaxed">
              Your data may be processed in countries outside your jurisdiction. When we transfer data internationally, we ensure appropriate safeguards are in place, including Standard Contractual Clauses approved by the European Commission.
            </p>
          </section>

          {/* 10. Children's Privacy */}
          <section>
            <h2 className="text-2xl font-bold text-gray-900 mb-4">10. Children's Privacy</h2>
            <p className="text-gray-700 leading-relaxed">
              Moreach is not intended for users under the age of 16. We do not knowingly collect personal information from children. If you believe we have collected information from a child, please contact us immediately.
            </p>
          </section>

          {/* 11. Changes to Privacy Policy */}
          <section>
            <h2 className="text-2xl font-bold text-gray-900 mb-4">11. Changes to This Policy</h2>
            <p className="text-gray-700 leading-relaxed">
              We may update this Privacy Policy from time to time. We will notify you of significant changes via email or through a prominent notice on our platform. Your continued use of the service after changes indicates acceptance of the updated policy.
            </p>
          </section>

          {/* Contact */}
          <section className="bg-gray-50 rounded-xl p-8 border border-gray-200 mt-12">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">Contact Us</h2>
            <p className="text-gray-700 leading-relaxed mb-4">
              If you have any questions or concerns about this Privacy Policy or our data practices, please contact our Data Protection Officer at:
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

