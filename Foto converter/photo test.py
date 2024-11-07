from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
from werkzeug.utils import secure_filename
import os
from PIL import Image

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Voor flash berichten
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_files():
    if 'files' not in request.files:
        flash('Geen bestanden geselecteerd')
        return redirect(request.url)

    files = request.files.getlist('files')
    target_width = int(request.form['width'])
    target_height = int(request.form['height'])
    converted_files = []  # Lijst om geconverteerde bestandsnamen op te slaan

    for file in files:
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            file.save(file_path)
            converted_filename = convert_image(file_path, target_width, target_height)
            converted_files.append(converted_filename)  # Voeg de geconverteerde bestandsnaam toe

    flash('Bestanden succesvol geüpload en geconverteerd!')
    return render_template('index.html', converted_files=converted_files)  # Geef de geconverteerde bestanden door aan de template

@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename, as_attachment=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'jpg', 'jpeg', 'png'}

def convert_image(file_path, target_width, target_height):
    with Image.open(file_path) as img:
        img = img.resize((target_width, target_height), Image.LANCZOS)
        converted_filename = file_path.replace('.jpg', '_converted.png').replace('.jpeg', '_converted.png').replace('.png', '_converted.png')
        img.save(converted_filename)
    return os.path.basename(converted_filename)  # Geef de naam van het geconverteerde bestand terug

if __name__ == "__main__":
    app.run(debug=True)
