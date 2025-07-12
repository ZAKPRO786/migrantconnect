import os
from datetime import datetime

from flask import Flask, request, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from gtts import gTTS  # Optional if you still want dummy TTS

from models import db, User, Document

# ----------------------------------------
# Workaround for OpenMP warning
# ----------------------------------------
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

# ----------------------------------------
# App config & folders
# ----------------------------------------
basedir = os.path.abspath(os.path.dirname(__file__))

UPLOAD_FOLDER = os.path.join(basedir, 'uploads')
INSTANCE_FOLDER = os.path.join(basedir, 'instance')

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(INSTANCE_FOLDER, exist_ok=True)

app = Flask(__name__)
CORS(app, origins=["https://infosys-hackathon-arch-angel.vercel.app/"])
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(INSTANCE_FOLDER, "migrantconnect.db")}'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

db.init_app(app)

# ----------------------------------------
# DB: Create tables
# ----------------------------------------
@app.before_first_request
def create_tables():
    db.create_all()

# ----------------------------------------
# Register
# ----------------------------------------
@app.route('/api/register', methods=['POST'])
def register():
    data = request.json

    name = data.get('name')
    phone = data.get('phone')
    email = data.get('email')
    password = data.get('password')
    user_type = data.get('user_type', 'migrant')

    if not name or not phone or not password:
        return jsonify({'error': 'Name, phone, and password are required'}), 400

    if User.query.filter_by(phone=phone).first():
        return jsonify({'error': 'Phone already registered'}), 400

    if email and User.query.filter_by(email=email).first():
        return jsonify({'error': 'Email already registered'}), 400

    hashed_password = generate_password_hash(password)

    user = User(
        name=name,
        phone=phone,
        email=email,
        password_hash=hashed_password,
        user_type=user_type
    )

    if user_type == 'migrant':
        user.id_type = data.get('id_type')
        user.id_number = data.get('id_number')
        user.nationality = data.get('nationality')
        user.current_location = data.get('current_location')
        user.languages = data.get('languages')
        dob_str = data.get('dob')
        if dob_str:
            try:
                user.dob = datetime.strptime(dob_str, "%Y-%m-%d").date()
            except ValueError:
                return jsonify({'error': 'Invalid date format for dob. Use YYYY-MM-DD.'}), 400
        user.gender = data.get('gender')
        user.emergency_contact = data.get('emergency_contact')

    elif user_type in ['hospital', 'school', 'government', 'ngo', 'firm']:
        user.org_name = data.get('org_name')
        user.org_type = data.get('org_type')
        user.org_subtype = data.get('org_subtype')
        user.org_registration_number = data.get('org_registration_number')
        user.org_address = data.get('org_address')
        user.org_contact_person = data.get('org_contact_person')
        user.org_contact_phone = data.get('org_contact_phone')

    else:
        return jsonify({'error': 'Invalid user_type'}), 400

    db.session.add(user)
    db.session.commit()

    return jsonify({'message': f'{user_type.capitalize()} registered successfully'})

# ----------------------------------------
# Login
# ----------------------------------------
@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    phone = data.get('phone')
    password = data.get('password')

    user = User.query.filter_by(phone=phone).first()
    if user and check_password_hash(user.password_hash, password):
        return jsonify({'message': 'Login successful', 'user_id': user.id})
    return jsonify({'error': 'Invalid credentials'}), 401

# ----------------------------------------
# Upload document
# ----------------------------------------
@app.route('/api/upload', methods=['POST'])
def upload_document():
    user_id = request.form.get('user_id')
    doc_type = request.form.get('doc_type')
    file = request.files.get('file')

    if not user_id or not doc_type or not file:
        return jsonify({'error': 'Missing data'}), 400

    filename = f"{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{file.filename}"
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    document = Document(user_id=user_id, doc_type=doc_type,
                        filename=filename, upload_date=datetime.utcnow())
    db.session.add(document)
    db.session.commit()

    return jsonify({'message': 'Document uploaded successfully'})

# ----------------------------------------
# Get user profile
# ----------------------------------------
@app.route('/api/user/<int:user_id>', methods=['GET'])
def get_user_profile(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    docs = [{
        'id': doc.id,
        'doc_type': doc.doc_type,
        'filename': doc.filename,
        'upload_date': doc.upload_date.isoformat()
    } for doc in user.documents]

    return jsonify({
        'name': user.name,
        'phone': user.phone,
        'email': user.email,
        'user_type': user.user_type,
        'id_type': user.id_type,
        'id_number': user.id_number,
        'nationality': user.nationality,
        'current_location': user.current_location,
        'languages': user.languages,
        'dob': user.dob.isoformat() if user.dob else None,
        'gender': user.gender,
        'emergency_contact': user.emergency_contact,
        'org_name': user.org_name,
        'org_type': user.org_type,
        'org_subtype': user.org_subtype,
        'org_registration_number': user.org_registration_number,
        'org_address': user.org_address,
        'org_contact_person': user.org_contact_person,
        'org_contact_phone': user.org_contact_phone,
        'documents': docs
    })

# ----------------------------------------
# Serve uploaded files
# ----------------------------------------
@app.route('/uploads/<filename>', methods=['GET'])
def get_document(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# ----------------------------------------
# Dummy Translate Text
# ----------------------------------------
@app.route('/api/translate', methods=['POST'])
def translate_text():
    data = request.json
    text = data.get('text', '')
    return jsonify({
        'translated_text': f"Translated '{text}' to Hindi (dummy response)",
        'speech_url': None
    })

# ----------------------------------------
# Dummy Voice-to-Voice Translate
# ----------------------------------------
@app.route('/api/voice-translate', methods=['POST'])
def voice_translate():
    return jsonify({
        'original_text': 'Dummy original speech-to-text.',
        'translated_text': 'Dummy translated speech.',
        'speech_url': None
    })

# ----------------------------------------
# Dummy DigiLocker Verify
# ----------------------------------------
@app.route('/api/verify-digilocker', methods=['POST'])
def verify_digilocker():
    data = request.json
    doc_number = data.get('doc_number')

    if doc_number == "1234567890":
        result = {'verified': True, 'message': 'Document verified successfully via DigiLocker (dummy)'}
    else:
        result = {'verified': False, 'message': 'Document not found in DigiLocker (dummy)'}

    return jsonify(result)

# ----------------------------------------
# BuddyConnect
# ----------------------------------------
@app.route('/api/buddyconnect/<int:user_id>', methods=['GET'])
def buddy_connect(user_id):
    user = User.query.get(user_id)
    if not user or user.user_type != 'migrant':
        return jsonify({'error': 'Invalid user'}), 404

    buddies = User.query.filter(
        User.user_type == 'migrant',
        User.nationality == user.nationality,
        User.id != user.id
    ).all()

    buddy_list = [{
        'id': b.id,
        'name': b.name,
        'phone': b.phone,
        'current_location': b.current_location
    } for b in buddies]

    return jsonify({'buddies': buddy_list})

# ----------------------------------------
# State Legal Info (simple)
# ----------------------------------------
@app.route('/api/legal-info/<state>', methods=['GET'])
def get_legal_info(state):
    legal_docs = {
        'Karnataka': 'https://your-site.com/legal/karnataka_migrant_welfare.pdf',
        'Maharashtra': 'https://your-site.com/legal/maharashtra_legal_aid.pdf'
    }
    doc = legal_docs.get(state, 'No legal info available for this state.')
    return jsonify({'legal_info': doc})

# ----------------------------------------
# Health check
# ----------------------------------------
@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'ok'})

# ----------------------------------------
if __name__ == '__main__':
    app.run(debug=True)
