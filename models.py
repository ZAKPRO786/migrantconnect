from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)

    # --------------------------------
    # Common fields (all users)
    # --------------------------------
    name = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True)
    password_hash = db.Column(db.String(128), nullable=False)

    user_type = db.Column(db.String(20), default='migrant')
    # Possible values: migrant, hospital, school, government, ngo, firm

    # --------------------------------
    # Migrant-specific fields
    # --------------------------------
    id_type = db.Column(db.String(50))         # Passport, Refugee ID, Aadhar, etc.
    id_number = db.Column(db.String(50), unique=True)
    nationality = db.Column(db.String(50))
    current_location = db.Column(db.String(255))
    languages = db.Column(db.String(255))      # Comma-separated
    dob = db.Column(db.Date)
    gender = db.Column(db.String(20))
    emergency_contact = db.Column(db.String(20))

    # --------------------------------
    # Organization-specific fields
    # --------------------------------
    org_name = db.Column(db.String(255))
    org_type = db.Column(db.String(100))       # Hospital, School, Government Office, Firm, NGO
    org_subtype = db.Column(db.String(100))    # Government, Private, NGO, Trust, etc.
    org_registration_number = db.Column(db.String(100), unique=True)
    org_address = db.Column(db.String(255))
    org_contact_person = db.Column(db.String(120))
    org_contact_phone = db.Column(db.String(20))

    # --------------------------------
    # Relationships
    # --------------------------------
    documents = db.relationship('Document', backref='owner', lazy=True)

    def __repr__(self):
        return f'<User {self.name} ({self.user_type})>'


class Document(db.Model):
    __tablename__ = 'documents'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    doc_type = db.Column(db.String(50))   # E.g., health record, work permit, etc.
    filename = db.Column(db.String(200))
    upload_date = db.Column(db.DateTime)

    def __repr__(self):
        return f'<Document {self.filename} for User {self.user_id}>'
