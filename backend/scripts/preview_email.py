#!/usr/bin/env python3
"""
Email Preview Script

Generates the poll summary email with mock data and opens it in browser.

Usage:
    cd backend
    python scripts/preview_email.py
"""

import webbrowser
import tempfile
import os
import sys

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings


def generate_preview_html():
    """Generate email HTML with mock data"""

    # Mock data
    total_leads_created = 67
    campaign_id = 1

    top_leads = [
        {"title": "Looking for a tool to find Reddit leads for my SaaS startup - any recommendations?", "subreddit_name": "SaaS", "relevancy_score": 98, "post_url": "#"},
        {"title": "How do you guys find potential customers on Reddit without being spammy?", "subreddit_name": "Entrepreneur", "relevancy_score": 96, "post_url": "#"},
        {"title": "Best practices for B2B lead generation in 2024?", "subreddit_name": "sales", "relevancy_score": 94, "post_url": "#"},
        {"title": "Need help automating my outreach - currently doing everything manually", "subreddit_name": "startups", "relevancy_score": 92, "post_url": "#"},
        {"title": "Anyone using AI tools for finding warm leads on social media?", "subreddit_name": "marketing", "relevancy_score": 91, "post_url": "#"},
        {"title": "Struggling to find product-market fit - where do you find early adopters?", "subreddit_name": "SaaS", "relevancy_score": 89, "post_url": "#"},
        {"title": "What's your lead gen stack? Looking for something more automated", "subreddit_name": "GrowthHacking", "relevancy_score": 87, "post_url": "#"},
        {"title": "How to identify high-intent buyers on Reddit?", "subreddit_name": "DigitalMarketing", "relevancy_score": 85, "post_url": "#"},
    ]

    # Build top leads cards - premium minimal design
    top_leads_cards = ""
    for lead in top_leads[:8]:
        score = lead.get("relevancy_score", 0)

        title = lead.get("title", "")[:65]
        if len(lead.get("title", "")) > 65:
            title += "..."

        post_url = lead.get("post_url", "#")
        subreddit = lead.get("subreddit_name", "")

        top_leads_cards += f"""
                                        <tr>
                                            <td style="padding: 0 0 10px 0;">
                                                <a href="{post_url}" style="text-decoration: none; display: block;">
                                                    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background-color: #fafafa; border-radius: 12px; border: 1px solid #f0f0f0;">
                                                        <tr>
                                                            <td style="padding: 14px 16px;">
                                                                <table role="presentation" width="100%" cellspacing="0" cellpadding="0">
                                                                    <tr>
                                                                        <td style="vertical-align: top; width: 40px;">
                                                                            <div style="width: 34px; height: 34px; background: linear-gradient(145deg, #f97316 0%, #ea580c 100%); border-radius: 8px; text-align: center; line-height: 34px;">
                                                                                <span style="color: #fff; font-size: 12px; font-weight: 700;">{score}</span>
                                                                            </div>
                                                                        </td>
                                                                        <td style="vertical-align: top; padding-left: 12px;">
                                                                            <div style="font-size: 13px; color: #1a1a1a; font-weight: 500; line-height: 1.4; margin-bottom: 3px;">{title}</div>
                                                                            <div style="font-size: 11px; color: #888; font-weight: 500;">r/{subreddit}</div>
                                                                        </td>
                                                                    </tr>
                                                                </table>
                                                            </td>
                                                        </tr>
                                                    </table>
                                                </a>
                                            </td>
                                        </tr>"""

    frontend_url = settings.FRONTEND_URL

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Email Preview - moreach.ai</title>
    </head>
    <body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Segoe UI', Roboto, sans-serif; background-color: #f8f8f8; -webkit-font-smoothing: antialiased;">
        <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="min-width: 100%; background-color: #f8f8f8;">
            <tr>
                <td align="center" style="padding: 48px 24px;">
                    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="max-width: 520px;">

                        <!-- Logo -->
                        <tr>
                            <td style="padding-bottom: 32px; text-align: center;">
                                <a href="{frontend_url}" style="text-decoration: none; display: inline-block;">
                                    <table role="presentation" cellspacing="0" cellpadding="0" style="margin: 0 auto;">
                                        <tr>
                                            <td style="padding-right: 8px; vertical-align: middle;">
                                                <img src="{frontend_url}/favicon-32x32.png" alt="" width="28" height="28" style="display: block; border-radius: 6px;">
                                            </td>
                                            <td style="vertical-align: middle;">
                                                <span style="font-size: 18px; font-weight: 600; color: #1a1a1a; letter-spacing: -0.3px;">moreach.ai</span>
                                            </td>
                                        </tr>
                                    </table>
                                </a>
                            </td>
                        </tr>

                        <!-- Main Card -->
                        <tr>
                            <td>
                                <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background-color: #ffffff; border-radius: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.04), 0 6px 16px rgba(0,0,0,0.04);">

                                    <!-- Hero Section -->
                                    <tr>
                                        <td style="padding: 36px 40px 28px; text-align: center;">
                                            <div style="font-size: 14px; color: #1a1a1a; font-weight: 500; line-height: 1;">
                                                We just discovered <span style="font-size: 22px; font-weight: 700; color: #f97316; vertical-align: baseline; position: relative; top: 1px;">{total_leads_created}</span> fresh leads for you
                                            </div>
                                        </td>
                                    </tr>

                                    <!-- Divider -->
                                    <tr>
                                        <td style="padding: 0 40px;">
                                            <div style="height: 1px; background: linear-gradient(90deg, transparent 0%, #e8e8e8 20%, #e8e8e8 80%, transparent 100%);"></div>
                                        </td>
                                    </tr>

                                    <!-- Top Leads Section -->
                                    <tr>
                                        <td style="padding: 32px 40px 24px;">
                                            <div style="font-size: 11px; font-weight: 600; color: #f97316; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 16px;">Top Matches</div>
                                            <table role="presentation" width="100%" cellspacing="0" cellpadding="0">
                                                {top_leads_cards}
                                            </table>
                                        </td>
                                    </tr>

                                    <!-- CTA Button -->
                                    <tr>
                                        <td style="padding: 16px 40px 48px; text-align: center;">
                                            <a href="{frontend_url}/reddit?view=leads&id={campaign_id}"
                                               style="display: inline-block; padding: 14px 36px; background: linear-gradient(180deg, #2a2a2a 0%, #1a1a1a 100%); color: #ffffff; text-decoration: none; font-size: 14px; font-weight: 600; border-radius: 12px; letter-spacing: -0.2px; box-shadow: 0 2px 4px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.08);">
                                                View All Leads
                                            </a>
                                        </td>
                                    </tr>
                                </table>
                            </td>
                        </tr>

                        <!-- Footer -->
                        <tr>
                            <td style="padding: 32px 0 0; text-align: center;">
                                <p style="margin: 0; font-size: 12px; color: #a0a0a0; font-weight: 400;">
                                    Sent by <a href="{frontend_url}" style="color: #8b8b8b; text-decoration: none; font-weight: 500;">moreach.ai</a>
                                </p>
                            </td>
                        </tr>

                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """

    return html_content


def main():
    print("🎨 Generating email preview...")

    html = generate_preview_html()

    # Save to temp file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
        f.write(html)
        filepath = f.name

    print(f"✅ Preview saved to: {filepath}")
    print("🌐 Opening in browser...")

    # Open in browser
    webbrowser.open(f'file://{filepath}')

    print("\n📧 Email preview opened in your default browser!")
    print("   Press Ctrl+C to exit.\n")

    # Keep script running so user can see the message
    try:
        input("Press Enter to clean up and exit...")
    except KeyboardInterrupt:
        pass

    # Clean up
    os.unlink(filepath)
    print("🧹 Cleaned up temp file.")


if __name__ == "__main__":
    main()
