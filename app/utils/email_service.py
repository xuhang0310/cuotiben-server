import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from app.core.config import settings
import json
from tencentcloud.common import credential
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.profile.http_profile import HttpProfile
from tencentcloud.ses.v20201002 import ses_client, models


def send_verification_email(email: str, verification_code: str) -> bool:
    """
    Send verification email to user using Tencent Cloud Email API
    """
    try:
        # Try to send via Tencent Cloud Email API first
        success = send_tencent_cloud_email(
            email=email,
            template_id="verification_template",  # This would be your actual template ID
            template_params=[verification_code, "10"]  # code and validity period in minutes
        )

        if success:
            return True
        else:
            # Fallback to SMTP if API fails
            return send_smtp_email(
                email=email,
                subject="邮箱验证 - 验证码",
                body=f"""
                您好！

                感谢您注册我们的服务。您的邮箱验证码是：

                {verification_code}

                此验证码将在10分钟内有效。

                如果您没有进行此操作，请忽略此邮件。

                谢谢！
                """
            )

    except Exception as e:
        print(f"Error sending verification email: {str(e)}")
        return False


def send_password_reset_email(email: str, reset_token: str) -> bool:
    """
    Send password reset email to user using Tencent Cloud Email API
    """
    try:
        reset_link = f"{settings.SERVER_DOMAIN}/reset-password?token={reset_token}"

        # Try to send via Tencent Cloud Email API first
        success = send_tencent_cloud_email(
            email=email,
            template_id="password_reset_template",  # This would be your actual template ID
            template_params=[reset_link, "24"]  # reset link and validity period in hours
        )

        if success:
            return True
        else:
            # Fallback to SMTP if API fails
            return send_smtp_email(
                email=email,
                subject="密码重置 - 重置链接",
                body=f"""
                您好！

                我们收到了您重置密码的请求。请点击以下链接重置您的密码：

                {reset_link}

                此链接将在24小时内有效。

                如果您没有进行此操作，请忽略此邮件。

                谢谢！
                """
            )

    except Exception as e:
        print(f"Error sending password reset email: {str(e)}")
        return False


def send_tencent_cloud_email(email: str, template_id: str, template_params: list) -> bool:
    """
    Send email using Tencent Cloud Email API
    """
    try:
        # Check if Tencent Cloud Email settings are configured
        if not settings.TENCENT_EMAIL_APP_ID or not settings.TENCENT_EMAIL_APP_KEY:
            print("Tencent Cloud Email not configured, falling back to SMTP")
            return False

        # Initialize credentials
        cred = credential.Credential(settings.TENCENT_EMAIL_APP_ID, settings.TENCENT_EMAIL_APP_KEY)

        # Configure HTTP profile
        httpProfile = HttpProfile()
        httpProfile.endpoint = "ses.tencentcloudapi.com"

        # Configure client profile
        clientProfile = ClientProfile()
        clientProfile.httpProfile = httpProfile

        # Create client instance
        client = ses_client.SesClient(cred, "ap-beijing", clientProfile)

        # Create request instance
        req = models.SendEmailRequest()

        # Set parameters
        params = {
            "FromEmailAddress": settings.TENCENT_EMAIL_SENDER,
            "Destination": [email],
            "Template": {
                "TemplateID": template_id,
                "TemplateData": json.dumps({
                    "code": template_params[0],  # verification code or reset link
                    "validity_period": template_params[1]  # validity period
                })
            },
            "Subject": "Verification Email" if "verification" in template_id.lower() else "Password Reset"
        }
        req.from_json_string(json.dumps(params))

        # Call the API
        resp = client.SendEmail(req)

        # Check response
        if resp.RequestId:
            print(f"Email sent successfully to {email}, RequestId: {resp.RequestId}")
            return True
        else:
            print(f"Failed to send email to {email}")
            return False

    except Exception as e:
        print(f"Error sending email via Tencent Cloud API: {str(e)}")
        return False


def send_smtp_email(email: str, subject: str, body: str) -> bool:
    """
    Send email using SMTP as fallback
    """
    try:
        # Create message
        msg = MIMEMultipart()
        msg['From'] = settings.SMTP_USERNAME
        msg['To'] = email
        msg['Subject'] = subject

        msg.attach(MIMEText(body, 'plain', 'utf-8'))

        # Create SSL context
        context = ssl.create_default_context()

        # Connect to server and send email
        with smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT) as server:
            server.starttls(context=context)
            server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)

            text = msg.as_string()
            server.sendmail(settings.SMTP_USERNAME, email, text)

        return True
    except Exception as e:
        print(f"Error sending SMTP email: {str(e)}")
        return False