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
    subject = f"{total_leads_created} new leads found - moreach.ai"

    # Build top leads cards - premium minimal design
    top_leads_cards = ""
    for i, lead in enumerate(top_leads[:8]):
        score = int(lead.get("relevancy_score", 0))

        title = lead.get("title", "")[:65]
        if len(lead.get("title", "")) > 65:
            title += "..."

        subreddit = lead.get("subreddit_name", "")

        top_leads_cards += f"""
                                        <tr>
                                            <td style="padding: 0 0 10px 0;">
                                                <a href="{settings.FRONTEND_URL}/reddit?view=leads&id={campaign_id}" style="text-decoration: none; display: block;">
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

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Segoe UI', Roboto, sans-serif; background-color: #f8f8f8; -webkit-font-smoothing: antialiased;">
        <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="min-width: 100%; background-color: #f8f8f8;">
            <tr>
                <td align="center" style="padding: 48px 24px;">
                    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="max-width: 520px;">

                        <!-- Logo -->
                        <tr>
                            <td style="padding-bottom: 32px; text-align: center;">
                                <a href="{settings.FRONTEND_URL}" style="text-decoration: none; display: inline-block;">
                                    <table role="presentation" cellspacing="0" cellpadding="0" style="margin: 0 auto;">
                                        <tr>
                                            <td style="padding-right: 8px; vertical-align: middle;">
                                                <img src="{settings.FRONTEND_URL}/favicon-32x32.png" alt="" width="28" height="28" style="display: block; border-radius: 6px;">
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
                                    {f'''
                                    <tr>
                                        <td style="padding: 32px 40px 24px;">
                                            <div style="font-size: 11px; font-weight: 600; color: #f97316; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 16px;">Top Matches</div>
                                            <table role="presentation" width="100%" cellspacing="0" cellpadding="0">
                                                {top_leads_cards}
                                            </table>
                                        </td>
                                    </tr>
                                    ''' if top_leads else ''}

                                    <!-- CTA Button -->
                                    <tr>
                                        <td style="padding: 16px 40px 48px; text-align: center;">
                                            <a href="{settings.FRONTEND_URL}/reddit?view=leads&id={campaign_id}"
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
                                    Sent by <a href="{settings.FRONTEND_URL}" style="color: #8b8b8b; text-decoration: none; font-weight: 500;">moreach.ai</a>
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
