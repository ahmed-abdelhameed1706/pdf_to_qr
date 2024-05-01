import os
from flask import Flask, request, send_file
import qrcode

app = Flask(__name__)

# Define a folder for temporary storage of PDFs and QR codes
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/')
def index():
    # Form to upload PDFs
    return '''
    <form method="post" enctype="multipart/form-data" action="/upload">
        <input type="file" name="pdf">
        <input type="submit" value="Upload PDF">
    </form>
    '''

@app.route('/upload', methods=['POST'])
def upload():
    if 'pdf' not in request.files:
        return "No file part"
    
    pdf_file = request.files['pdf']
    if pdf_file.filename == '':
        return "No selected file"
    
    # Get the base file name without extension
    base_filename = os.path.splitext(pdf_file.filename)[0]
    
    # Save the uploaded PDF
    pdf_path = os.path.join(UPLOAD_FOLDER, pdf_file.filename)
    pdf_file.save(pdf_path)
    
    # Create a URL for the PDF download
    pdf_url = request.host_url + "download-pdf/" + pdf_file.filename
    
    # Generate a QR code with the URL for the PDF
    qr = qrcode.make(pdf_url)
    
    # Name the QR code file using the base file name + "_QR.png"
    qr_filename = f"{base_filename}_QR.png"
    qr_path = os.path.join(UPLOAD_FOLDER, qr_filename)
    qr.save(qr_path)
    
    # Provide a link to download the QR code
    return f'''
    <p>PDF uploaded! <a href="{pdf_url}">Download PDF</a></p>
    <p><a href="/download-qr-code/{qr_filename}">Download QR Code</a></p>
    <img src="/view-qr-code/{qr_filename}" alt="QR Code" />
    '''

@app.route('/view-qr-code/<qr_filename>')
def view_qr_code(qr_filename):
    # Return the QR code image for viewing
    return send_file(os.path.join(UPLOAD_FOLDER, qr_filename))

@app.route('/download-qr-code/<qr_filename>')
def download_qr_code(qr_filename):
    # Serve the QR code for download
    return send_file(os.path.join(UPLOAD_FOLDER, qr_filename), as_attachment=True)

@app.route('/download-pdf/<filename>')
def download_pdf(filename):
    # Serve the PDF for download
    pdf_path = os.path.join(UPLOAD_FOLDER, filename)
    return send_file(pdf_path, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
