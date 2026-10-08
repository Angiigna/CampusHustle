import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'campushustle-super-secret-key-2026'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or f"sqlite:///{os.path.join(BASE_DIR, 'campushustle.db')}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Fare Engine Constants
    DEFAULT_FARE = 25.0
    ACCEPTANCE_TIMEOUT_SECONDS = 60
