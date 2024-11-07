from flask import Flask, render_template, request, redirect, url_for
import os
from PIL import Image

app = Flask(__name__)

# Map om geüploade bestanden op te slaan
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')  # Render de index.html

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return 'No file part'
    file = request.files['file']
    if file.filename == '':
        return 'No selected file'
    
    # Sla het bestand op
    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(file_path)

    # Hier kun je de logica voor het converteren van de afbeelding toevoegen
    # Voorbeeld: Converteer naar een andere indeling (bijv. PNG)
    img = Image.open(file_path)
    converted_file_path = os.path.join(UPLOAD_FOLDER, f'converted_{file.filename}.png')
    img.save(converted_file_path, 'PNG')

    return f'File uploaded and converted successfully! <a href="{url_for("uploaded_file", filename=f"converted_{file.filename}.png")}">Download here</a>'

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

if __name__ == '__main__':
    app.run(debug=True)