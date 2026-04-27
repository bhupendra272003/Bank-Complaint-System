import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import database as db
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ========================================
# EMAIL CONFIGURATION - FROM ENV VARIABLES
# ========================================
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL")    # CHANGE: Admin email daal

def send_email_notification(to_email, complaint_id, customer_name, complaint_text, category, priority):
    try:
        subject = f"🏦 Bank Complaint Update: {complaint_id} - {category}"
        
        body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; }}
                .container {{ max-width: 600px; margin: auto; background: white; border-radius: 10px; overflow: hidden; }}
                .header {{ background: linear-gradient(135deg, #4361ee, #764ba2); color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; }}
                .info-box {{ background: #f8f9fa; padding: 15px; border-radius: 8px; margin: 15px 0; }}
                .info-item {{ margin: 10px 0; }}
                .info-label {{ font-weight: bold; color: #4361ee; width: 120px; display: inline-block; }}
                .priority-high {{ color: #dc3545; font-weight: bold; }}
                .priority-medium {{ color: #ffc107; font-weight: bold; }}
                .priority-low {{ color: #28a745; font-weight: bold; }}
                .complaint-text {{ background: #f8f9fa; padding: 15px; border-radius: 8px; border-left: 4px solid #4361ee; }}
                .footer {{ background: #f8f9fa; padding: 15px; text-align: center; font-size: 12px; }}
                .btn {{ background: #4361ee; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>🏦 Bank Complaint System</h2>
                </div>
                <div class="content">
                    <h3>🔔 New Complaint Registered</h3>
                    <div class="info-box">
                        <div class="info-item"><span class="info-label">Complaint ID:</span> {complaint_id}</div>
                        <div class="info-item"><span class="info-label">Customer:</span> {customer_name}</div>
                        <div class="info-item"><span class="info-label">Category:</span> {category}</div>
                        <div class="info-item"><span class="info-label">Priority:</span> <span class="priority-{priority.lower().replace(' ', '-')}">{priority}</span></div>
                    </div>
                    <div class="complaint-text">
                        <strong>💬 Complaint:</strong><br>
                        {complaint_text}
                    </div>
                    <div style="text-align: center; margin-top: 20px;">
                        <a href="http://localhost:5000/login" class="btn">View Dashboard</a>
                    </div>
                </div>
                <div class="footer">
                    <p>Bank Complaint Management System - Automated Notification</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        msg = MIMEMultipart()
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'html'))
        
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()
        
        db.save_notification(complaint_id, 'email', to_email, 'sent')
        print(f"✅ Email sent to {to_email}")
        return True
        
    except Exception as e:
        print(f"❌ Email error: {e}")
        db.save_notification(complaint_id, 'email', to_email, f'failed: {e}')
        return False

def notify_admin_and_customer(complaint_id, customer_name, customer_email, customer_mobile, complaint_text, category, priority):
    notifications_sent = []
    
    # Email to Admin
    if ADMIN_EMAIL:
        print(f"📧 Sending to Admin: {ADMIN_EMAIL}")
        if send_email_notification(ADMIN_EMAIL, complaint_id, customer_name, complaint_text, category, priority):
            notifications_sent.append('admin_email')
    
    # Email to Customer
    if customer_email:
        print(f"📧 Sending to Customer: {customer_email}")
        if send_email_notification(customer_email, complaint_id, customer_name, complaint_text, category, priority):
            notifications_sent.append('customer_email')
    
    print(f"✅ Notifications: {notifications_sent}")
    return notifications_sent