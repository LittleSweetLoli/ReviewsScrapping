from dotenv import load_dotenv
import os

#load_dotenv('.env')

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY')
    MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')  # Env или fallback
