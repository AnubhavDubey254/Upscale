import os
import sys
import uuid 
from werkzeug.utils import secure_filename 
from flask import Flask, jsonify, send_from_directory, request, abort 
from flask_cors import CORS 
from flask_sqlalchemy import SQLAlchemy 
from PIL import Image # For image processing/validation
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)
from processor import process_image_for_upscale

# --- UTILITY FUNCTION ---
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'} 

def allowed_file(filename):
    """Checks if the file extension is allowed."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# --- CONFIGURATION ---
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
FRONTEND_DIST_DIR = os.path.join(BASE_DIR, 'dist')
# Define paths for originals folder (make sure this folder exists!)
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads', 'originals') 

app = Flask(
    __name__, 
    static_folder=FRONTEND_DIST_DIR, 
    static_url_path='/static'       
)
CORS(app) 

# Database Configuration for SQLite
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(BASE_DIR, 'app.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# --- FILE SECURITY CONFIGURATION ---
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
# Set max file size to 16 MB (16 * 1024 * 1024 bytes)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024 
# ---------------------------------------

db = SQLAlchemy(app) 

# --- DATABASE MODELS ---
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128)) 

    def __repr__(self):
        return f'<User {self.username}>'

class FileHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    
    original_filename = db.Column(db.String(255), nullable=False)
    processed_filename = db.Column(db.String(255), nullable=True) 
    
    status = db.Column(db.String(50), default='PENDING', nullable=False) 
    uploaded_at = db.Column(db.DateTime, default=db.func.now())
    
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('files', lazy=True))

    def __repr__(self):
        return f'<File {self.original_filename} - Status: {self.status}>'
# -----------------------


# --- API ROUTES ---

@app.route('/api/data')
def get_data():
    """Simple test API endpoint."""
    return jsonify({
        "message": "Hello from the Flask backend!",
        "status": "API is working with SQLite configured"
    })


@app.route('/api/upload', methods=['POST'])
def upload_file():
    # 1. Basic Request Validation
    if 'file' not in request.files:
        return jsonify({"message": "No file part in the request"}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({"message": "No selected file"}), 400

    # 2. File Extension and Type Validation
    if not allowed_file(file.filename):
        return jsonify({"message": "File type not allowed"}), 400
    
    # 3. Security and Unique Naming
    original_filename_secure = secure_filename(file.filename)
    _, file_ext = os.path.splitext(original_filename_secure) 
    unique_filename_base = str(uuid.uuid4())
    unique_filename_server = unique_filename_base + file_ext

    # 4. Save File and Create DB Record
    try:
        # Save the original file to the 'originals' folder
        save_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename_server)
        file.save(save_path)
        
        # Create a new FileHistory record...
        new_file = FileHistory(
            original_filename=file.filename,
            user_id=1,
            status='PENDING',
            processed_filename=unique_filename_server 
        )
        db.session.add(new_file)
        db.session.commit()
        
        # 5. NEW: Call the Image Processor and Update Status
        success = process_image_for_upscale(unique_filename_server)
        
        if success:
            new_file.status = 'COMPLETED'
            db.session.commit()
            message = "File uploaded and processed successfully."
            
        else:
            new_file.status = 'FAILED'
            db.session.commit()
            message = "File uploaded, but processing failed."
            
        # 6. Return Success/Failure Response
        return jsonify({
            "message": message, 
            "filename": unique_filename_base,
            "status": new_file.status.lower()
        }), 201

    except Exception as e:
        # Handles errors like MAX_CONTENT_LENGTH exceeded
        db.session.rollback()
        print(f"Upload error: {e}")
        return jsonify({"message": f"Upload failed due to server error: {str(e)}", "status": "error"}), 500

@app.route('/api/download/<string:unique_filename_base>', methods=['GET'])
def download_file(unique_filename_base):
    """
    Securely serves the processed file to the user based on its unique ID.
    """
    
    try:
        # 1. Look up the file record in the database
        # We search using the unique base name (UUID)
        file_record = FileHistory.query.filter(
            FileHistory.processed_filename.like(f'{unique_filename_base}%')
        ).first()

        if not file_record:
            return jsonify({"message": "File not found."}), 404
            
        # 2. Check Processing Status
        if file_record.status != 'COMPLETED':
            return jsonify({"message": f"File is still {file_record.status.lower()}."}), 409 # 409 Conflict
            
        # 3. Define File Paths
        file_name_on_server = file_record.processed_filename
        
        # NOTE: Set the directory to the PROCESSED folder, not the UPLOAD folder
        processed_dir = os.path.join(app.config['UPLOAD_FOLDER'], '..', 'processed')
        
        # 4. Securely send the file for download
        return send_from_directory(
            processed_dir,
            file_name_on_server,
            as_attachment=True, # Forces the browser to download the file instead of displaying it
            download_name=f"upscaled_{file_record.original_filename}" # Gives the downloaded file a friendly name
        )

    except Exception as e:
        print(f"Download error: {e}")
        return jsonify({"message": "An error occurred during download."}), 500
# --- FRONTEND SERVING (PRODUCTION MODE) ---
# This serves the built Vite application files when running in production.

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_frontend(path):
    """Serves the index.html for SPA routing."""
    
    # Try to serve a specific static asset directly
    if path != "" and os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    
    # Otherwise, serve the main index.html for React Router to handle the route
    else:
        return send_from_directory(app.static_folder, 'index.html')


if __name__ == '__main__':
    app.run(debug=True)