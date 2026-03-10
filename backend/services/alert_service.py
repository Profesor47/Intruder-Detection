"""
Alert Service
Email notifications with optional video clips for intrusion detection
"""

import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import Optional, List
from datetime import datetime
import os

logger = logging.getLogger(__name__)


class AlertService:
    """Email alert management for GUARDZILLA."""
    
    def __init__(
        self,
        smtp_server: str = "smtp.gmail.com",
        smtp_port: int = 587,
        sender_email: str = "",
        sender_password: str = ""
    ):
        """Initialize alert service."""
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.sender_email = sender_email
        self.sender_password = sender_password
        self.configured = bool(sender_email and sender_password)
        
        if self.configured:
            logger.info("✓ Alert service configured")
        else:
            logger.warning("Alert service not configured (missing credentials)")
    
    def send_intruder_alert(
        self,
        recipient_email: str,
        detection_data: dict,
        video_clip_path: Optional[str] = None,
        snapshot_path: Optional[str] = None
    ) -> bool:
        """
        Send intrusion detection alert.
        
        Args:
            recipient_email: Recipient email address
            detection_data: Detection information
            video_clip_path: Optional path to video clip
            snapshot_path: Optional path to snapshot image
        
        Returns:
            True if sent successfully
        """
        if not self.configured:
            logger.warning("Alert service not configured")
            return False
        
        try:
            # Create email
            msg = MIMEMultipart("alternative")
            msg["Subject"] = "GUARDZILLA: INTRUDER ALERT"
            msg["From"] = self.sender_email
            msg["To"] = recipient_email
            
            # Create email body
            detection_time = detection_data.get("timestamp", datetime.now().isoformat())
            confidence = detection_data.get("confidence", 0)
            
            text = f"""
            INTRUDER ALERT!
            
            An unknown person has been detected by GUARDZILLA security system.
            
            Detection Details:
            - Time: {detection_time}
            - Confidence: {confidence:.2%}
            - Location: Premises
            
            Please check the attached image for more details.
            Review the full video clip in your GUARDZILLA dashboard.
            
            Stay Safe,
            GUARDZILLA Security System
            """
            
            html = f"""
            <html>
              <body style="font-family: Arial, sans-serif;">
                <h2 style="color: red;">🚨 INTRUDER ALERT!</h2>
                <p>An unknown person has been detected by GUARDZILLA security system.</p>
                
                <h3>Detection Details:</h3>
                <ul>
                  <li><strong>Time:</strong> {detection_time}</li>
                  <li><strong>Confidence:</strong> {confidence:.2%}</li>
                  <li><strong>Status:</strong> Active Monitoring</li>
                </ul>
                
                <p style="color: gray; font-size: 12px;">
                  Please review the attached snapshot and full video in your GUARDZILLA dashboard.
                </p>
              </body>
            </html>
            """
            
            part1 = MIMEText(text, "plain")
            part2 = MIMEText(html, "html")
            
            msg.attach(part1)
            msg.attach(part2)
            
            # Attach snapshot if available
            if snapshot_path and os.path.exists(snapshot_path):
                try:
                    with open(snapshot_path, "rb") as attachment:
                        part = MIMEBase("application", "octet-stream")
                        part.set_payload(attachment.read())
                    
                    encoders.encode_base64(part)
                    part.add_header(
                        "Content-Disposition",
                        f"attachment; filename= snapshot.jpg"
                    )
                    msg.attach(part)
                except Exception as e:
                    logger.error(f"Failed to attach snapshot: {str(e)}")
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.send_message(msg)
            
            logger.info(f"Alert sent to {recipient_email}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to send alert: {str(e)}")
            return False
    
    def send_test_alert(self, recipient: str) -> bool:
        """Send test alert email."""
        if not self.configured:
            return False
        
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = "GUARDZILLA: Test Alert"
            msg["From"] = self.sender_email
            msg["To"] = recipient
            
            text = """
            This is a test alert from GUARDZILLA security system.
            
            If you received this email, your alert system is working correctly!
            
            GUARDZILLA
            """
            
            html = """
            <html>
              <body style="font-family: Arial, sans-serif;">
                <h2>✓ GUARDZILLA Test Alert</h2>
                <p>This is a test alert from GUARDZILLA security system.</p>
                <p style="color: green;"><strong>If you received this email, your alert system is working correctly!</strong></p>
              </body>
            </html>
            """
            
            part1 = MIMEText(text, "plain")
            part2 = MIMEText(html, "html")
            
            msg.attach(part1)
            msg.attach(part2)
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.send_message(msg)
            
            logger.info(f"Test alert sent to {recipient}")
            return True
        
        except Exception as e:
            logger.error(f"Test alert failed: {str(e)}")
            return False
    
    def send_daily_report(
        self,
        recipient_email: str,
        statistics: dict
    ) -> bool:
        """Send daily security report."""
        if not self.configured:
            return False
        
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = "GUARDZILLA: Daily Security Report"
            msg["From"] = self.sender_email
            msg["To"] = recipient_email
            
            total_detections = statistics.get("total_detections", 0)
            intruder_count = statistics.get("intruders", 0)
            known_faces = statistics.get("known_faces", 0)
            uptime = statistics.get("uptime", "N/A")
            
            text = f"""
            GUARDZILLA Daily Security Report
            
            Date: {datetime.now().strftime('%Y-%m-%d')}
            
            Statistics:
            - Total Detections: {total_detections}
            - Intruders Detected: {intruder_count}
            - Known Faces: {known_faces}
            - System Uptime: {uptime}
            
            Your system is operating normally.
            """
            
            html = f"""
            <html>
              <body style="font-family: Arial, sans-serif;">
                <h2>GUARDZILLA Daily Security Report</h2>
                <p><strong>Date:</strong> {datetime.now().strftime('%Y-%m-%d')}</p>
                
                <h3>Daily Statistics:</h3>
                <table style="border-collapse: collapse;">
                  <tr>
                    <td style="border: 1px solid #ddd; padding: 8px;"><strong>Total Detections</strong></td>
                    <td style="border: 1px solid #ddd; padding: 8px;">{total_detections}</td>
                  </tr>
                  <tr>
                    <td style="border: 1px solid #ddd; padding: 8px;"><strong>Intruders Detected</strong></td>
                    <td style="border: 1px solid #ddd; padding: 8px;">{intruder_count}</td>
                  </tr>
                  <tr>
                    <td style="border: 1px solid #ddd; padding: 8px;"><strong>Known Faces</strong></td>
                    <td style="border: 1px solid #ddd; padding: 8px;">{known_faces}</td>
                  </tr>
                  <tr>
                    <td style="border: 1px solid #ddd; padding: 8px;"><strong>System Uptime</strong></td>
                    <td style="border: 1px solid #ddd; padding: 8px;">{uptime}</td>
                  </tr>
                </table>
                
                <p style="margin-top: 20px; color: green;">Your system is operating normally.</p>
              </body>
            </html>
            """
            
            part1 = MIMEText(text, "plain")
            part2 = MIMEText(html, "html")
            
            msg.attach(part1)
            msg.attach(part2)
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.send_message(msg)
            
            logger.info(f"Daily report sent to {recipient_email}")
            return True
        
        except Exception as e:
            logger.error(f"Daily report failed: {str(e)}")
            return False
