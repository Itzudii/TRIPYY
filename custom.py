import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class smtpData:
    def authormail():
        return "udityasage2004@gmail.com"
    
    def secretkey():
        return "ciafpdofuqfctryu"
    
    def providermail():
        return "smtp.gmail.com"
    
    def send_email(self,recipient_email,otp):
        try:
            msg = MIMEMultipart()
            msg["From"] = self.authormail()
            msg["To"] = recipient_email
            msg["Subject"] = "Tripyy | registration OTP"
            body = f"Your OTP is {otp}."
            msg.attach(MIMEText(body, "plain"))
    
            SMTP_SERVER = self.providermail()  
            SMTP_PORT = 587  # 465 for SSL, 25 for non-secure
            EMAIL_ADDRESS = self.authormail()
            EMAIL_PASSWORD = self.secretkey()
            
            # Connect to SMTP server
            server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
            server.starttls()  # Secure the connection
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.sendmail(EMAIL_ADDRESS, recipient_email, msg.as_string())
            server.quit()
    
            print(f"Email sent successfully to {recipient_email}!")
        except Exception as e:
            print(f"Error: {e}")
    
def coordkey():
    return 'Zl6uQG-1R_LuHSw9jdlDODppJXGeZoLlLTuFzK5-HFk'

def forcastkey():
    return "7180dc0bb496bc0c7c13ac2f5b400824"

def poikey():
    return "1f1bd843d6cf4a41a4eacdd3b2b6fe1d"

    
