"""
Email service using SendGrid for sending verification and notification emails
"""
import logging
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content

from app.core.config import settings

logger = logging.getLogger(__name__)


def send_email(to_email: str, subject: str, html_content: str) -> bool:
    """Send an email using SendGrid"""
    if not settings.SENDGRID_API_KEY:
        logger.warning("SENDGRID_API_KEY not configured, skipping email send")
        return False

    try:
        message = Mail(
            from_email=Email(settings.SENDGRID_FROM_EMAIL, "moreach.ai"),
            to_emails=To(to_email),
            subject=subject,
            html_content=Content("text/html", html_content)
        )

        sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
        response = sg.send(message)

        if response.status_code in (200, 201, 202):
            logger.info(f"Email sent successfully to {to_email}")
            return True
        else:
            logger.error(f"Failed to send email: {response.status_code}")
            return False

    except Exception as e:
        logger.error(f"Error sending email: {str(e)}")
        return False


def send_verification_email(to_email: str, verification_token: str) -> bool:
    """Send email verification email with a verification link"""
    verification_url = f"{settings.FRONTEND_URL}/verify-email?token={verification_token}"

    subject = "Verify your email - moreach.ai"

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; background-color: #f5f5f5;">
        <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="min-width: 100%; background-color: #f5f5f5;">
            <tr>
                <td align="center" style="padding: 40px 20px;">
                    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="max-width: 600px; background-color: #ffffff; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.05);">
                        <!-- Header -->
                        <tr>
                            <td style="padding: 40px 40px 30px; text-align: center; border-bottom: 1px solid #eee;">
                                <h1 style="margin: 0; font-size: 28px; font-weight: 700; color: #111;">moreach.ai</h1>
                            </td>
                        </tr>

                        <!-- Content -->
                        <tr>
                            <td style="padding: 40px;">
                                <h2 style="margin: 0 0 20px; font-size: 24px; font-weight: 600; color: #111;">Verify your email</h2>
                                <p style="margin: 0 0 24px; font-size: 16px; line-height: 1.6; color: #444;">
                                    Thanks for signing up for moreach.ai! Please verify your email address by clicking the button below.
                                </p>

                                <!-- CTA Button -->
                                <table role="presentation" width="100%" cellspacing="0" cellpadding="0">
                                    <tr>
                                        <td style="padding: 10px 0 30px;">
                                            <a href="{verification_url}"
                                               style="display: inline-block; padding: 14px 32px; background-color: #111; color: #ffffff; text-decoration: none; font-size: 16px; font-weight: 600; border-radius: 8px;">
                                                Verify Email Address
                                            </a>
                                        </td>
                                    </tr>
                                </table>

                                <p style="margin: 0 0 16px; font-size: 14px; line-height: 1.6; color: #666;">
                                    If the button doesn't work, copy and paste this link into your browser:
                                </p>
                                <p style="margin: 0 0 24px; font-size: 14px; line-height: 1.6; color: #666; word-break: break-all;">
                                    <a href="{verification_url}" style="color: #0066cc;">{verification_url}</a>
                                </p>

                                <p style="margin: 0; font-size: 14px; line-height: 1.6; color: #999;">
                                    This link will expire in 24 hours. If you didn't create an account, you can safely ignore this email.
                                </p>
                            </td>
                        </tr>

                        <!-- Footer -->
                        <tr>
                            <td style="padding: 30px 40px; border-top: 1px solid #eee; text-align: center;">
                                <p style="margin: 0; font-size: 13px; color: #999;">
                                    &copy; 2026 moreach.ai
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

    return send_email(to_email, subject, html_content)


def send_welcome_email(to_email: str, full_name: str) -> bool:
    """Send welcome email after successful verification"""
    subject = "Welcome to moreach.ai!"

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; background-color: #f5f5f5;">
        <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="min-width: 100%; background-color: #f5f5f5;">
            <tr>
                <td align="center" style="padding: 40px 20px;">
                    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="max-width: 600px; background-color: #ffffff; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.05);">
                        <!-- Header -->
                        <tr>
                            <td style="padding: 40px 40px 30px; text-align: center; border-bottom: 1px solid #eee;">
                                <h1 style="margin: 0; font-size: 28px; font-weight: 700; color: #111;">moreach.ai</h1>
                            </td>
                        </tr>

                        <!-- Content -->
                        <tr>
                            <td style="padding: 40px;">
                                <h2 style="margin: 0 0 20px; font-size: 24px; font-weight: 600; color: #111;">Welcome, {full_name}!</h2>
                                <p style="margin: 0 0 24px; font-size: 16px; line-height: 1.6; color: #444;">
                                    Your email has been verified and your account is now active. You can now start discovering leads across social platforms.
                                </p>

                                <!-- CTA Button -->
                                <table role="presentation" width="100%" cellspacing="0" cellpadding="0">
                                    <tr>
                                        <td style="padding: 10px 0 30px;">
                                            <a href="{settings.FRONTEND_URL}/login"
                                               style="display: inline-block; padding: 14px 32px; background-color: #111; color: #ffffff; text-decoration: none; font-size: 16px; font-weight: 600; border-radius: 8px;">
                                                Get Started
                                            </a>
                                        </td>
                                    </tr>
                                </table>

                                <p style="margin: 0; font-size: 14px; line-height: 1.6; color: #666;">
                                    If you have any questions, feel free to reach out to us.
                                </p>
                            </td>
                        </tr>

                        <!-- Footer -->
                        <tr>
                            <td style="padding: 30px 40px; border-top: 1px solid #eee; text-align: center;">
                                <p style="margin: 0; font-size: 13px; color: #999;">
                                    &copy; 2026 moreach.ai
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

    return send_email(to_email, subject, html_content)


def send_poll_summary_email(
    to_email: str,
    campaign_name: str,
    total_posts_fetched: int,
    total_leads_created: int,
    high_quality_count: int,
    top_leads: list,
    campaign_id: int
) -> bool:
    """
    Send email summary after Reddit polling task completes

    Args:
        to_email: User's email address
        campaign_name: Name/description of the campaign
        total_posts_fetched: Total number of posts scanned
        total_leads_created: Number of new leads created (score >= 50)
        high_quality_count: Number of leads with score 80+
        top_leads: List of top 10 leads with title, subreddit_name, relevancy_score, post_url
        campaign_id: Campaign ID for building the "View Leads" link
    """
    subject = f"🎯 {total_leads_created} new leads discovered - moreach.ai"

    # Build top leads rows
    top_leads_rows = ""
    for i, lead in enumerate(top_leads[:10]):
        score = lead.get("relevancy_score", 0)
        # Color based on score
        if score >= 90:
            score_color = "#22c55e"
            score_bg = "#f0fdf4"
        elif score >= 80:
            score_color = "#84cc16"
            score_bg = "#f7fee7"
        else:
            score_color = "#eab308"
            score_bg = "#fefce8"

        title = lead.get("title", "")[:80]
        if len(lead.get("title", "")) > 80:
            title += "..."

        top_leads_rows += f"""
        <tr>
            <td style="padding: 14px 16px; border-bottom: 1px solid #f0f0f0;">
                <div style="font-size: 14px; color: #111; font-weight: 500; line-height: 1.4; margin-bottom: 6px;">{title}</div>
                <div style="font-size: 12px; color: #666;">
                    <span style="color: #f97316; font-weight: 500;">r/{lead.get("subreddit_name", "")}</span>
                    <span style="margin: 0 6px; color: #ddd;">•</span>
                    <span style="display: inline-block; padding: 2px 6px; background-color: {score_bg}; color: {score_color}; border-radius: 4px; font-weight: 600; font-size: 11px;">{score}</span>
                </div>
            </td>
        </tr>"""

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; background-color: #f5f5f5;">
        <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="min-width: 100%; background-color: #f5f5f5;">
            <tr>
                <td align="center" style="padding: 40px 20px;">
                    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="max-width: 600px; background-color: #ffffff; border-radius: 16px; box-shadow: 0 4px 12px rgba(0,0,0,0.08);">
                        <!-- Header with Logo -->
                        <tr>
                            <td style="padding: 28px 40px; text-align: center; border-bottom: 1px solid #f0f0f0;">
                                <a href="{settings.FRONTEND_URL}" style="text-decoration: none;">
                                    <table role="presentation" cellspacing="0" cellpadding="0" style="margin: 0 auto;">
                                        <tr>
                                            <td style="padding-right: 10px; vertical-align: middle;">
                                                <div style="width: 36px; height: 36px; background: linear-gradient(135deg, #111 0%, #333 100%); border-radius: 10px; display: flex; align-items: center; justify-content: center;">
                                                    <span style="color: #fff; font-size: 18px; font-weight: 700;">m</span>
                                                </div>
                                            </td>
                                            <td style="vertical-align: middle;">
                                                <span style="font-size: 22px; font-weight: 800; color: #111; letter-spacing: -0.5px;">moreach.ai</span>
                                            </td>
                                        </tr>
                                    </table>
                                </a>
                            </td>
                        </tr>

                        <!-- Main Content -->
                        <tr>
                            <td style="padding: 36px 40px;">
                                <!-- Big Number Hero -->
                                <div style="background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%); border-radius: 16px; padding: 32px; text-align: center; margin-bottom: 24px;">
                                    <div style="font-size: 64px; font-weight: 800; color: #22c55e; line-height: 1; letter-spacing: -2px;">{total_leads_created}</div>
                                    <div style="font-size: 15px; color: #666; margin-top: 8px; font-weight: 500;">new leads discovered</div>
                                </div>

                                <!-- Stats Row -->
                                <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="margin-bottom: 28px;">
                                    <tr>
                                        <td style="text-align: center; padding: 16px; background-color: #f9fafb; border-radius: 12px 0 0 12px;">
                                            <div style="font-size: 24px; font-weight: 700; color: #111;">{total_posts_fetched}</div>
                                            <div style="font-size: 12px; color: #666; margin-top: 2px;">posts scanned</div>
                                        </td>
                                        <td style="text-align: center; padding: 16px; background-color: #fefce8; border-radius: 0 12px 12px 0;">
                                            <div style="font-size: 24px; font-weight: 700; color: #854d0e;">{high_quality_count}</div>
                                            <div style="font-size: 12px; color: #a16207; margin-top: 2px;">high-quality (80+)</div>
                                        </td>
                                    </tr>
                                </table>

                                <!-- Top Leads Section -->
                                {f'''
                                <h3 style="margin: 0 0 14px; font-size: 14px; font-weight: 700; color: #111; text-transform: uppercase; letter-spacing: 0.5px;">🔥 Top Leads</h3>
                                <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="border: 1px solid #e5e5e5; border-radius: 12px; overflow: hidden; margin-bottom: 28px;">
                                    {top_leads_rows}
                                </table>
                                ''' if top_leads else ''}

                                <!-- CTA Button -->
                                <table role="presentation" width="100%" cellspacing="0" cellpadding="0">
                                    <tr>
                                        <td style="text-align: center;">
                                            <a href="{settings.FRONTEND_URL}/reddit?view=leads&id={campaign_id}"
                                               style="display: inline-block; padding: 16px 48px; background-color: #111; color: #ffffff; text-decoration: none; font-size: 15px; font-weight: 600; border-radius: 10px; letter-spacing: 0.3px;">
                                                View All Leads →
                                            </a>
                                        </td>
                                    </tr>
                                </table>
                            </td>
                        </tr>

                        <!-- Footer -->
                        <tr>
                            <td style="padding: 20px 40px; border-top: 1px solid #f0f0f0; text-align: center;">
                                <p style="margin: 0; font-size: 12px; color: #999;">
                                    <a href="{settings.FRONTEND_URL}" style="color: #666; text-decoration: none;">moreach.ai</a>
                                    <span style="margin: 0 8px; color: #ddd;">•</span>
                                    Find leads on Reddit, effortlessly
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

    return send_email(to_email, subject, html_content)
