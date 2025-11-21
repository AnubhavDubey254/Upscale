import os
import sys
import uuid 
from werkzeug.utils import secure_filename 
from flask import Flask, jsonify, send_from_directory, request, abort 
from flask_cors import CORS 
from flask_sqlalchemy import SQLAlchemy 
from PIL import Image # For image processing/validation

# --- PATH FIX FOR RELATIVE IMPORTS ---
# Ensures 'processor' can be imported regardless of how the script is run
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from processor import process_image_for_upscale
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required 
from flask_bcrypt import Bcrypt

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

# Enable CORS with support for credentials (cookies) for Auth
CORS(app, supports_credentials=True)

app.config['SECRET_KEY'] = '123456789'  # Replace with a secure key in production!
# Database Configuration for SQLite
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(BASE_DIR, 'app.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# --- INITIALIZE EXTENSIONS ---
bcrypt = Bcrypt(app)
login_manager = LoginManager()
login_manager.init_app(app) 
login_manager.session_protection = "strong"
login_manager.login_view = 'login' 
login_manager.login_message_category = "info"

# --- FILE SECURITY CONFIGURATION ---
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
# Set max file size to 16 MB (16 * 1024 * 1024 bytes)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024 
# ---------------------------------------

db = SQLAlchemy(app) 

# --- DATABASE MODELS ---
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128)) 

    def set_password(self, password):
        """Hashes the password and stores it securely."""
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        """Returns True if the password matches the hash, False otherwise."""
        return bcrypt.check_password_hash(self.password_hash, password)

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

@login_manager.user_loader
def load_user(user_id):
    """Callback function used to reload the user object from the user ID stored in the session."""
    return db.session.get(User, int(user_id))

@app.route('/api/data')
def get_data():
    """Simple test API endpoint."""
    return jsonify({
        "message": "Hello from the Flask backend!",
        "status": "API is working with SQLite configured"
    })

# --- AUTHENTICATION ROUTES ---

@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    if not username or not email or not password:
        return jsonify({"message": "Missing required fields"}), 400

    if User.query.filter_by(username=username).first() or User.query.filter_by(email=email).first():
        return jsonify({"message": "User already exists"}), 409

    new_user = User(username=username, email=email)
    new_user.set_password(password)

    db.session.add(new_user)
    db.session.commit()

    return jsonify({"message": "User registered successfully"}), 201

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    user = User.query.filter_by(email=email).first()

    if user and user.check_password(password):
        login_user(user) # Flask-Login creates the session cookie here
        return jsonify({"message": "Login successful", "username": user.username}), 200
    
    return jsonify({"message": "Invalid email or password"}), 401

@app.route('/api/logout', methods=['POST'])
@login_required
def logout():
    logout_user() 
    return jsonify({"message": "Logged out successfully"}), 200

@app.route('/api/check-auth', methods=['GET'])
def check_auth():
    """Helper endpoint for frontend to check if user is logged in."""
    if current_user.is_authenticated:
        return jsonify({"authenticated": True, "username": current_user.username, "id": current_user.id}), 200
    else:
        return jsonify({"authenticated": False}), 200

# --- FILE HANDLING ROUTES ---

@app.route('/api/upload', methods=['POST'])
@login_required # Block guests from uploading
def upload_file():
    if 'file' not in request.files:
        return jsonify({"message": "No file part"}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({"message": "No selected file"}), 400

    if not allowed_file(file.filename):
        return jsonify({"message": "File type not allowed"}), 400
    
    # Secure and Unique Naming
    original_filename_secure = secure_filename(file.filename)
    _, file_ext = os.path.splitext(original_filename_secure) 
    unique_filename_base = str(uuid.uuid4())
    unique_filename_server = unique_filename_base + file_ext

    try:
        # Save Original
        save_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename_server)
        file.save(save_path)
        
        # Create DB Record linked to current_user
        new_file = FileHistory(
            original_filename=file.filename,
            user_id=current_user.id, # Use the real logged-in user
            status='PENDING',
            processed_filename=unique_filename_server 
        )
        db.session.add(new_file)
        db.session.commit()
        
        # Process Image
        success = process_image_for_upscale(unique_filename_server)
        
        if success:
            new_file.status = 'COMPLETED'
            db.session.commit()
            message = "File uploaded and processed successfully."
        else:
            new_file.status = 'FAILED'
            db.session.commit()
            message = "File uploaded, but processing failed."
            
        return jsonify({
            "message": message, 
            "filename": unique_filename_base,
            "status": new_file.status.lower()
        }), 201

    except Exception as e:
        db.session.rollback()
        print(f"Upload error: {e}")
        return jsonify({"message": f"Upload failed: {str(e)}", "status": "error"}), 500

@app.route('/api/history', methods=['GET'])
@login_required
def get_user_history():
    """Returns the list of uploaded files for the logged-in user."""
    try:
        files = FileHistory.query.filter_by(user_id=current_user.id)\
            .order_by(FileHistory.uploaded_at.desc())\
            .all()
        
        history_data = [{
            'id': f.id,
            'original_filename': f.original_filename,
            'unique_id': f.processed_filename.split('.')[0] if f.processed_filename else None,
            'status': f.status,
            'date': f.uploaded_at.strftime('%Y-%m-%d %H:%M')
        } for f in files]

        return jsonify(history_data), 200
    except Exception as e:
        print(f"History error: {e}")
        return jsonify({"message": "Could not fetch history"}), 500

# 👇 NEW ROUTE: DELETE HISTORY ITEM
@app.route('/api/history/<int:file_id>', methods=['DELETE'])
@login_required
def delete_history_item(file_id):
    """Deletes a file history record and the associated physical files."""
    try:
        # Find the record ensuring it belongs to the current user
        file_record = FileHistory.query.filter_by(id=file_id, user_id=current_user.id).first()

        if not file_record:
            return jsonify({"message": "File not found or access denied"}), 404

        # 1. Delete Original File
        if file_record.processed_filename:
            original_path = os.path.join(app.config['UPLOAD_FOLDER'], file_record.processed_filename)
            if os.path.exists(original_path):
                os.remove(original_path)

            # 2. Delete Processed File
            processed_path = os.path.join(app.config['UPLOAD_FOLDER'], '..', 'processed', file_record.processed_filename)
            if os.path.exists(processed_path):
                os.remove(processed_path)

        # 3. Delete Database Record
        db.session.delete(file_record)
        db.session.commit()

        return jsonify({"message": "File deleted successfully"}), 200

    except Exception as e:
        print(f"Delete error: {e}")
        return jsonify({"message": "Error deleting file"}), 500

@app.route('/api/download/<string:unique_filename_base>', methods=['GET'])
def download_file(unique_filename_base):
    """Securely serves the PROCESSED file for download."""
    try:
        file_record = FileHistory.query.filter(
            FileHistory.processed_filename.like(f'{unique_filename_base}%')
        ).first()

        if not file_record:
            return jsonify({"message": "File not found."}), 404
            
        if file_record.status != 'COMPLETED':
            return jsonify({"message": f"File is still {file_record.status.lower()}."}), 409
            
        # Define path to processed folder
        processed_dir = os.path.join(app.config['UPLOAD_FOLDER'], '..', 'processed')
        
        return send_from_directory(
            processed_dir,
            file_record.processed_filename,
            as_attachment=True,
            download_name=f"upscaled_{file_record.original_filename}"
        )
    except Exception as e:
        print(f"Download error: {e}")
        return jsonify({"message": "Download error"}), 500

@app.route('/api/view/<string:unique_filename_base>', methods=['GET'])
def view_file(unique_filename_base):
    """
    Serves the ORIGINAL file for inline display (thumbnail/preview).
    """
    try:
        file_record = FileHistory.query.filter(
            FileHistory.processed_filename.like(f'{unique_filename_base}%')
        ).first()

        if not file_record:
            return jsonify({"message": "File not found."}), 404
            
        # Serve from the ORIGINALS folder
        return send_from_directory(
            app.config['UPLOAD_FOLDER'],
            file_record.processed_filename, 
            as_attachment=False # Allow browser display
        )
    except Exception as e:
        print(f"Preview error: {e}")
        return jsonify({"message": "Error loading preview."}), 500

# --- FRONTEND SERVING (PRODUCTION MODE) ---

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_frontend(path):
    """Serves the index.html for SPA routing."""
    if path != "" and os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, 'index.html')

if __name__ == '__main__':
    with app.app_context():
        db.create_all() # Create tables if they don't exist
    app.run(debug=True)