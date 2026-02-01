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
    subreddit_distribution: dict,
    relevancy_distribution: dict,
    campaign_id: int
) -> bool:
    """
    Send email summary after Reddit polling task completes

    Args:
        to_email: User's email address
        campaign_name: Name/description of the campaign
        total_posts_fetched: Total number of posts scanned
        total_leads_created: Number of new leads created (score >= 50)
        subreddit_distribution: Dict of subreddit -> count, e.g. {"SaaS": 15, "startups": 10}
        relevancy_distribution: Dict of score tier -> count, e.g. {"90+": 5, "80-89": 12}
        campaign_id: Campaign ID for building the "View Leads" link
    """
    subject = f"moreach.ai - {total_leads_created} new leads from Reddit"

    # Build subreddit distribution rows
    subreddit_rows = ""
    for sub, count in sorted(subreddit_distribution.items(), key=lambda x: -x[1]):
        subreddit_rows += f"""
        <tr>
            <td style="padding: 10px 16px; border-bottom: 1px solid #f0f0f0; font-size: 14px; color: #333;">r/{sub}</td>
            <td style="padding: 10px 16px; border-bottom: 1px solid #f0f0f0; font-size: 14px; color: #333; text-align: right; font-weight: 600;">{count}</td>
        </tr>"""

    # Build relevancy distribution rows with color coding
    relevancy_rows = ""
    tier_colors = {
        "90+": "#22c55e",      # Green for excellent
        "80-89": "#84cc16",    # Light green for strong
        "70-79": "#eab308",    # Yellow for good
        "60-69": "#f97316",    # Orange for moderate
        "50-59": "#6b7280",    # Gray for weak
    }
    for tier in ["90+", "80-89", "70-79", "60-69", "50-59"]:
        count = relevancy_distribution.get(tier, 0)
        if count > 0:
            color = tier_colors.get(tier, "#6b7280")
            relevancy_rows += f"""
            <tr>
                <td style="padding: 10px 16px; border-bottom: 1px solid #f0f0f0; font-size: 14px;">
                    <span style="display: inline-block; padding: 2px 8px; background-color: {color}22; color: {color}; border-radius: 4px; font-weight: 600;">{tier}</span>
                </td>
                <td style="padding: 10px 16px; border-bottom: 1px solid #f0f0f0; font-size: 14px; color: #333; text-align: right; font-weight: 600;">{count}</td>
            </tr>"""

    # Calculate high-quality leads (80+)
    high_quality = relevancy_distribution.get("90+", 0) + relevancy_distribution.get("80-89", 0)

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
                        <!-- Header with Logo -->
                        <tr>
                            <td style="padding: 32px 40px; text-align: center; border-bottom: 1px solid #eee;">
                                <table role="presentation" cellspacing="0" cellpadding="0" style="margin: 0 auto;">
                                    <tr>
                                        <td style="padding-right: 8px;">
                                            <div style="width: 32px; height: 32px; background-color: #111; border-radius: 8px; display: inline-block;"></div>
                                        </td>
                                        <td>
                                            <span style="font-size: 24px; font-weight: 700; color: #111;">moreach.ai</span>
                                        </td>
                                    </tr>
                                </table>
                            </td>
                        </tr>

                        <!-- Main Content -->
                        <tr>
                            <td style="padding: 40px;">
                                <!-- Hero Message -->
                                <p style="margin: 0 0 8px; font-size: 16px; color: #666; line-height: 1.5;">
                                    We just scanned <strong style="color: #111;">{total_posts_fetched} posts</strong> across your monitored subreddits and found:
                                </p>

                                <!-- Big Number -->
                                <div style="background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%); border-radius: 12px; padding: 28px; text-align: center; margin: 20px 0;">
                                    <div style="font-size: 56px; font-weight: 700; color: #22c55e; line-height: 1;">{total_leads_created}</div>
                                    <div style="font-size: 16px; color: #666; margin-top: 8px;">new leads discovered</div>
                                </div>

                                <!-- High Quality Highlight -->
                                {f'''
                                <div style="background-color: #fefce8; border-left: 4px solid #eab308; padding: 14px 16px; margin-bottom: 28px; border-radius: 0 8px 8px 0;">
                                    <span style="font-weight: 600; color: #854d0e;">{high_quality} high-quality leads</span>
                                    <span style="color: #a16207;"> with relevancy score 80+</span>
                                </div>
                                ''' if high_quality > 0 else ''}

                                <!-- Subreddit Distribution -->
                                <h3 style="margin: 0 0 12px; font-size: 15px; font-weight: 600; color: #111;">By Subreddit</h3>
                                <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="border: 1px solid #e5e5e5; border-radius: 8px; overflow: hidden; margin-bottom: 24px;">
                                    {subreddit_rows}
                                </table>

                                <!-- Relevancy Distribution -->
                                <h3 style="margin: 0 0 12px; font-size: 15px; font-weight: 600; color: #111;">By Relevancy Score</h3>
                                <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="border: 1px solid #e5e5e5; border-radius: 8px; overflow: hidden;">
                                    {relevancy_rows}
                                </table>

                                <!-- CTA Button -->
                                <table role="presentation" width="100%" cellspacing="0" cellpadding="0">
                                    <tr>
                                        <td style="padding: 32px 0 0; text-align: center;">
                                            <a href="{settings.FRONTEND_URL}/reddit?view=leads&id={campaign_id}"
                                               style="display: inline-block; padding: 14px 40px; background-color: #111; color: #ffffff; text-decoration: none; font-size: 16px; font-weight: 600; border-radius: 8px;">
                                                View More
                                            </a>
                                        </td>
                                    </tr>
                                </table>
                            </td>
                        </tr>

                        <!-- Footer -->
                        <tr>
                            <td style="padding: 24px 40px; border-top: 1px solid #eee; text-align: center;">
                                <p style="margin: 0; font-size: 12px; color: #999;">
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
