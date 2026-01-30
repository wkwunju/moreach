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
                                    &copy; 2024 moreach.ai - AI-Powered Lead Discovery
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
                                    &copy; 2024 moreach.ai - AI-Powered Lead Discovery
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
