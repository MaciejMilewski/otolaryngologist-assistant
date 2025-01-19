from datetime import datetime

from flask_login import UserMixin
from sqlalchemy import Index

# from flask_sqlalchemy import SQLAlchemy
# db = SQLAlchemy()

from app import db


class Patient(db.Model):
    __tablename__ = 'patient'
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    surname = db.Column(db.String(50), nullable=False)
    pesel = db.Column(db.String(11), unique=True, nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    state = db.Column(db.String(50), nullable=False)
    city = db.Column(db.String(50), nullable=False)
    street = db.Column(db.String(50))
    apartment_number = db.Column(db.String(10), nullable=False)

    # Relacja z Visit
    visits = db.relationship('Visit', backref='patient', lazy='select')
    audiograms = db.relationship('Audiogram', backref='patient', lazy='select')
    certificates = db.relationship('MedicalCertificate', backref='patient', lazy=True)


class User(db.Model, UserMixin):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    login = db.Column(db.String(50), unique=True, nullable=False)
    pwd = db.Column(db.String(100), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    date_joined = db.Column(db.Date, default=lambda : datetime.utcnow().date(), nullable=False)
    isActive = db.Column(db.Boolean, default=True, nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)

    def __init__(self, login, name, pwd, email, is_admin, is_active):
        self.login = login
        self.name = name
        self.pwd = pwd
        self.email = email
        self.is_admin = is_admin
        self.isActive = is_active

    def __repr__(self):
        return '<User %r>' % self.login

    def is_active(self):
        return self.isActive


class Visit(db.Model):
    __tablename__ = 'visit'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=False, index=True)
    diagnosis = db.Column(db.String(255), nullable=False)
    location = db.Column(db.String(100), nullable=False)
    interview = db.Column(db.Text, nullable=False)
    general_info = db.Column(db.Text, nullable=False)
    orl = db.Column(db.String(100), nullable=False)
    examination = db.Column(db.String, nullable=False)
    recommendations = db.Column(db.String, nullable=False)
    whisper_test = db.Column(db.String)
    nfz_info = db.Column(db.String(255))
    examination_date = db.Column(db.Date, nullable=False)
    routine = db.Column(db.String)
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    # Relacja z Audiogram
    audiograms = db.relationship('Audiogram', backref='visit', lazy='select')


class Audiogram(db.Model):
    __tablename__ = 'audiogram'
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=False, index=True)
    visit_id = db.Column(db.Integer, db.ForeignKey('visit.id'), nullable=True, index=True)
    audiogram_date = db.Column(db.Date, nullable=False)
    ul_250 = db.Column(db.Integer, nullable=False)
    ul_500 = db.Column(db.Integer, nullable=False)
    ul_1000 = db.Column(db.Integer, nullable=False)
    ul_2000 = db.Column(db.Integer, nullable=False)
    ul_3000 = db.Column(db.Integer, nullable=False)
    ul_4000 = db.Column(db.Integer, nullable=False)
    ul_6000 = db.Column(db.Integer, nullable=False)
    ul_8000 = db.Column(db.Integer, nullable=False)
    up_250 = db.Column(db.Integer, nullable=False)
    up_500 = db.Column(db.Integer, nullable=False)
    up_1000 = db.Column(db.Integer, nullable=False)
    up_2000 = db.Column(db.Integer, nullable=False)
    up_3000 = db.Column(db.Integer, nullable=False)
    up_4000 = db.Column(db.Integer, nullable=False)
    up_6000 = db.Column(db.Integer, nullable=False)
    up_8000 = db.Column(db.Integer, nullable=False)


class MedicalCertificate(db.Model):
    __tablename__ = 'medical_certificate'
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), index=True, nullable=False)
    created_at = db.Column(db.Date, nullable=False)
    type = db.Column(db.INTEGER, nullable=False)
    info = db.Column(db.String, nullable=False)
    is_able_to_work = db.Column(db.Boolean, nullable=False)
    month = db.Column(db.Integer, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    location = db.Column(db.String, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    user = db.relationship('User', backref='medical_certificates', lazy=True)


class Procedure(db.Model):
    __tablename__ = 'procedure'
    id = db.Column(db.Integer, primary_key=True)
    icd9 = db.Column(db.String)
    group = db.Column(db.String)
    value = db.Column(db.Integer)
    title = db.Column(db.String, nullable=False)
    description = db.Column(db.String, nullable=False)


class Schedule(db.Model):
    __tablename__ = 'schedule'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String, nullable=False)
    description = db.Column(db.String)
    url = db.Column(db.String)
    color_back = db.Column(db.String)
    color_fore = db.Column(db.String)
    start_date = db.Column(db.Date, default=None, nullable=False)
    end_date = db.Column(db.Date, default=None, nullable=False)
    start_time = db.Column(db.String, default=None, nullable=False)
    end_time = db.Column(db.String, default=None, nullable=False)


Index('idx_patient_surname', Patient.surname)
Index('idx_medical_certificate_type', MedicalCertificate.type)
Index('idx_medical_certificate_month', MedicalCertificate.month)
Index('idx_medical_certificate_year', MedicalCertificate.year)
