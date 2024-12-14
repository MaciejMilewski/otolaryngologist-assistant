from sqlalchemy import Index

from app import db


class Patient(db.Model):
    __tablename__ = 'patient'
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    surname = db.Column(db.String(50), nullable=False)
    pesel = db.Column(db.String(11), unique=True, nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    state = db.Column(db.String(50))
    city = db.Column(db.String(50))
    street = db.Column(db.String(50))
    apartment_number = db.Column(db.String(10))


class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    login = db.Column(db.String(50), unique=True, nullable=False)
    pwd = db.Column(db.String(100), nullable=False)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)
    date_joined = db.Column(db.DateTime)
    isActive = db.Column(db.Boolean, default=True)
    is_admin = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return '<User %r>' % self.login

    def is_active(self):
        return self.isActive


class Visit(db.Model):
    __tablename__ = 'visit'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'))
    diagnosis = db.Column(db.String(255))
    location = db.Column(db.String(100))
    interview = db.Column(db.Text)
    general_info = db.Column(db.Text)
    orl = db.Column(db.String(100))
    examination = db.Column(db.String, nullable=False)
    recommendations = db.Column(db.String, nullable=False)
    whisper_test = db.Column(db.String, nullable=False)
    nfz_info = db.Column(db.String, nullable=False)
    audiogram_date = db.Column(db.Date, default=None)
    examination_date = db.Column(db.Date, default=None)
    routine = db.Column(db.String)
    ul_250 = db.Column(db.Integer)
    ul_500 = db.Column(db.Integer)
    ul_1000 = db.Column(db.Integer)
    ul_2000 = db.Column(db.Integer)
    ul_3000 = db.Column(db.Integer)
    ul_4000 = db.Column(db.Integer)
    ul_6000 = db.Column(db.Integer)
    ul_8000 = db.Column(db.Integer)
    up_250 = db.Column(db.Integer)
    up_500 = db.Column(db.Integer)
    up_1000 = db.Column(db.Integer)
    up_2000 = db.Column(db.Integer)
    up_3000 = db.Column(db.Integer)
    up_4000 = db.Column(db.Integer)
    up_6000 = db.Column(db.Integer)
    up_8000 = db.Column(db.Integer)


class MedicalCertificate(db.Model):
    __tablename__ = 'medical_certificate'
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'))
    created_at = db.Column(db.Date)
    type = db.Column(db.INTEGER)
    info = db.Column(db.String)
    is_able_to_work = db.Column(db.Boolean)
    month = db.Column(db.Integer)
    year = db.Column(db.Integer)


class Procedure(db.Model):
    __tablename__ = 'procedure'
    id = db.Column(db.Integer, primary_key=True)
    icd9 = db.Column(db.String)
    group = db.Column(db.String)
    value = db.Column(db.Integer)
    title = db.Column(db.String)
    description = db.Column(db.String)


class Schedule(db.Model):
    __tablename__ = 'schedule'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    title = db.Column(db.String)
    description = db.Column(db.String)
    url = db.Column(db.String)
    color_back = db.Column(db.String)
    color_fore = db.Column(db.String)
    start_date = db.Column(db.Date, default=None)
    end_date = db.Column(db.Date, default=None)
    start_time = db.Column(db.String, default=None)
    end_time = db.Column(db.String, default=None)


Index('idx_patient_surname', Patient.surname)
Index('idx_medical_certificate_type', MedicalCertificate.type)
Index('idx_medical_certificate_month', MedicalCertificate.month)
Index('idx_medical_certificate_year', MedicalCertificate.year)
