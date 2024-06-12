import logging

# logging.basicConfig(level=logging.INFO)
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

from crew import EmailProcessingCrew
from email_state import EmailState

import os
import imapclient
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import mailparse
import pika
from flask import Flask, jsonify, request
from flask_apscheduler import APScheduler
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text

from dotenv import load_dotenv



load_dotenv()

app = Flask(__name__)

# Database configuration from environment variables
db_user = os.getenv('DB_USERNAME')
db_pass = os.getenv('DB_PASSWORD')
db_host = os.getenv('DB_HOST')
db_name = os.getenv('DB_NAME')
db_port = os.getenv('DB_PORT')

# 正式环境数据连接配置
# app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://{db_user}:{db_pass}@{db_host}:3306/{db_name}'

# 本地环境数据库连接配置
app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


# 加载RabbitMQ配置
rabbitmq_host = os.getenv('RABBITMQ_HOST')
rabbitmq_queue = os.getenv('RABBITMQ_QUEUE')


# RabbitMQ 连接函数
def rabbitmq_connection():
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=rabbitmq_host))
    channel = connection.channel()
    channel.queue_declare(queue=rabbitmq_queue)
    return connection, channel


# 发送消息到队列
def send_to_queue(email_id):
    connection, channel = rabbitmq_connection()
    channel.basic_publish(exchange='',
                          routing_key=rabbitmq_queue,
                          body=email_id)
    print(f"Sent {email_id} to RabbitMQ")
    connection.close()



# Define models
class Email(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email_id = db.Column(db.String(255), primary_key=True)
    thread_id = db.Column(db.String(255), nullable=False)
    is_new = db.Column(db.Boolean, default=True)
    processed = db.Column(db.Boolean, default=False)  # To track whether the email has been processed
    tag_id = db.Column(db.Integer, db.ForeignKey('tag.tag_id'))
    snippet = db.Column(db.String(255), nullable=False)
    sender = db.Column(db.String(255), nullable=False)

class Tag(db.Model):
    tag_id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(255), nullable=False)

# Configuration for APScheduler
class Config:
    SCHEDULER_API_ENABLED = True

app.config.from_object(Config())

# Initialize scheduler
scheduler = APScheduler()
scheduler.init_app(app)
scheduler.start()

state = EmailState() # new

class MailWorkflow:
    def __init__(self):
        self.imap_host = os.getenv('IMAP_SERVER')
        self.imap_port = int(os.getenv('IMAP_PORT'))
        self.imap_user = os.getenv('IMAP_USERNAME')
        self.imap_pass = os.getenv('IMAP_PASSWORD')
        self.smtp_host = os.getenv('MAIL_SERVER')
        self.smtp_port = int(os.getenv('MAIL_PORT'))
        self.smtp_user = os.getenv('MAIL_USERNAME')
        self.smtp_pass = os.getenv('MAIL_PASSWORD')
        self.email_processor = EmailProcessingCrew()

    def fetch_emails(self):
        try:
            logging.debug("Attempting to connect to email server..")
            with imapclient.IMAPClient(self.imap_host, port=self.imap_port, ssl=True) as client:
                client.login(self.imap_user, self.imap_pass)
                logging.debug(f"Connected to server:{self.imap_host}")
                client.select_folder('INBOX')
                messages = client.search('UNSEEN')
                logging.debug(f"Fetched {len(messages)} emails.")
                if messages:
                    for msg_id, data in client.fetch(messages, 'RFC822').items():
                        email = mailparse.parse_from_bytes(data[b'RFC822'])
                        email_id = email.message_id
                        self.process_email(email,email_id)
                        logging.info(f"Received email with subject: {email['subject']}")
                else:
                    logging.info("No new emails found.")
        except Exception as e:
            logging.error("Failed to fetch emails.", exc_info=True)

    def process_email(self, email, email_id):
        try:
            # Use EmailProcessor to process email content
            response = self.email_processor.process_email(email.text_plain[0])
            logging.info(f"Processing email: {email.subject}")
            logging.info(f"EmailProcessor response: {response}")

            # Mark email as processed and save to database
            existing_email = Email.query.filter_by(email_id=email_id).first()
            if existing_email:
                existing_email.processed = True
                # db.session.commit()
            else:
                new_email = Email(
                    email_id=email_id,
                    thread_id=email.message_id,
                    snippet=email.text_plain[0],
                    sender=email.from_
                )
                db.session.add(new_email)
            db.session.commit()
            logging.info(f"Email {email_id} saved to database")

            # Format email for processing crew
            formatted_email = {
                "id": email_id,
                "threadId": email.message_id,  # Ensure this is correct attribute
                "snippet": email.text_plain[0],  # Simplified example
                "sender": email.from_  # Ensure this is correct attribute
            }

            state.add_email(formatted_email)

            # Kickoff email processing with EmailProcessingCrew
            # state = {"emails": [formatted_email]}  # This structure may need adjustment based on EmailProcessingCrew requirements
            result = self.email_crew.kickoff({"emails":[formatted_email]})
            logging.info("Result from EmailProcessingCrew:", result)

            # Send email ID to a message queue or another processing module
            self.send_to_next_process(email_id)
    
        except Exception as e:
            logging.error(f"Error processing email {email_id}: {e}", exc_info=True)

    def send_to_next_process(self, email_id):
        # Example: Send email ID to a message queue or directly invoke another module
        # Here you would implement actual messaging logic, such as publishing to a message queue.
        send_to_queue(email_id)
        print(f"Email ID {email_id} sent to the next process.")


        
    def send_email(self, to_email, subject, body):
        msg = MIMEMultipart()
        msg['From'] = self.smtp_user
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        with smtplib.SMTP_SSL(self.smtp_host, self.smtp_port) as server:
            server.login(self.smtp_user, self.smtp_pass)
            server.sendmail(self.smtp_user, to_email, msg.as_string())

@app.route('/')
def index():
    return jsonify({"message": "Mail workflow service is running"})
# Email processing and database interaction would go here

@app.route('/send', methods=['POST'])
def send():
    data = request.json
    to_email = data.get('to_email')
    subject = data.get('subject')
    body = data.get('body')
    workflow = MailWorkflow()
    workflow.send_email(to_email, subject, body)
    return jsonify({"message": "Email sent successfully"})

@app.route('/health', methods=['GET'])
def health_check():
    try:
        # 尝试执行一个简单的数据库查询
        db.session.execute(text('SELECT 1'))
        return jsonify({"status": "healthy", "db": "connected"}), 200
    except Exception as e:
        return jsonify({"status": "unhealthy", "db": "disconnected", "error": str(e)}), 500


if __name__ == "__main__":
    with app.app_context():
        db.create_all()  # Ensure all tables are created    
    app.run(host='0.0.0.0', port=5000)



# Schedule the job to run every 5 minutes
@scheduler.task('interval', id='fetch_emails', minutes=5)
def job1():
    workflow = MailWorkflow()
    workflow.fetch_emails()
