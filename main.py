import os
from flask import Flask, request, send_file, render_template_string
import qrcode
import boto3
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

app = Flask(__name__)

# AWS configuration
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_KEY")
AWS_BUCKET_NAME = "pdftoqr"

# S3 client configuration
s3 = boto3.client(
    "s3",
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
)

# Temporary storage folder
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route("/")
def index():
    return '''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Upload Any file and Generate QR Code By AJV</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                margin: 0;
                padding: 0;
            }
            .container {
                max-width: 600px;
                margin: 0 auto;
                padding: 20px;
                text-align: center;
            }
            form {
                margin-bottom: 20px;
            }
            input[type="file"] {
                display: block;
                margin: 10px auto;
            }
            input[type="submit"] {
                padding: 10px 20px;
                background-color: #007BFF;
                color: white;
                border: none;
                border-radius: 5px;
                cursor: pointer;
            }
            a {
                text-decoration: none;
                color: #007BFF;
            }
            a:hover {
                text-decoration: underline;
            }
            img {
                max-width: 100%;
                height: auto;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Upload Any File and Generate QR Code By AJV</h1>
            <form method="post" enctype="multipart/form-data" action="/upload">
                <input type="file" name="pdf" required>
                <input type="submit" value="Upload File">
            </form>
        </div>
    </body>
    </html>
    '''

@app.route("/upload", methods=["POST"])
def upload():
    if "pdf" not in request.files:
        return "No file part"
    
    pdf_file = request.files["pdf"]
    if pdf_file.filename == "":
        return "No selected file"
    
    # Secure filename to avoid path traversal
    filename = secure_filename(pdf_file.filename)
    
    # Upload the PDF to S3
    s3.upload_fileobj(pdf_file, AWS_BUCKET_NAME, filename)
    
    # Generate a URL to download the PDF from S3
    pdf_url = f"https://{AWS_BUCKET_NAME}.s3.amazonaws.com/{filename}"
    
    # Generate a QR code with the URL to the PDF
    qr = qrcode.make(pdf_url)
    
    # Save the QR code and upload it to S3
    qr_filename = f"{os.path.splitext(filename)[0]}_QR.png"
    qr_path = os.path.join(UPLOAD_FOLDER, qr_filename)
    qr.save(qr_path)
    
    s3.upload_file(qr_path, AWS_BUCKET_NAME, qr_filename)
    
    # Return download links and the QR code image
    return render_template_string(
        '''
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>File Upload and QR Code Generation</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    margin: 0;
                    padding: 0;
                }
                .container {
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                    text-align: center;
                }
                a {
                    text-decoration: none;
                    color: #007BFF;
                }
                a:hover {
                    text-decoration: underline;
                }
                img {
                    max-width: 100%;
                    height: auto;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <p>File and QR code uploaded successfully!</p>
                <a href="/download-pdf/{{ filename }}">Download File</a>
                |
                <a href="/download-qr-code/{{ qr_filename }}">Download QR Code</a>
                <br>
                <img src="/view-qr-code/{{ qr_filename }}" alt="QR Code" />
            </div>
        </body>
        </html>
        ''',
        filename=filename,
        qr_filename=qr_filename,
    )

@app.route("/download-pdf/<filename>")
def download_pdf(filename):
    # Download the PDF from S3 and serve it
    local_path = os.path.join(UPLOAD_FOLDER, filename)
    s3.download_file(AWS_BUCKET_NAME, filename, local_path)
    return send_file(
        local_path,
        as_attachment=True,
        download_name=filename
    )

@app.route("/download-qr-code/<qr_filename>")
def download_qr_code(qr_filename):
    # Download the QR code from S3 and serve it
    local_path = os.path.join(UPLOAD_FOLDER, qr_filename)
    s3.download_file(AWS_BUCKET_NAME, qr_filename, local_path)
    return send_file(
        local_path,
        as_attachment=True,
        download_name=qr_filename
    )

@app.route("/view-qr-code/<qr_filename>")
def view_qr_code(qr_filename):
    # Serve the QR code image for viewing
    local_path = os.path.join(UPLOAD_FOLDER, qr_filename)
    s3.download_file(AWS_BUCKET_NAME, qr_filename, local_path)
    return send_file(local_path, mimetype="image/png")

if __name__ == '__main__':
    app.run(debug=True)
