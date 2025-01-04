import os


class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', '03496583AGD@&KW0H')
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(BASE_DIR, 'instance', 'ENT.DB')}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    #  SQLALCHEMY_ECHO = True

