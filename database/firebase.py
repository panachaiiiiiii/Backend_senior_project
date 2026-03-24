import firebase_admin
from firebase_admin import credentials, db
import os, json

def get_db():
    if not firebase_admin._apps:
        firebase_key = os.getenv("FIREBASE_KEY")

        if not firebase_key:
            raise Exception("FIREBASE_KEY not found")

        cred_dict = json.loads(firebase_key)

        cred = credentials.Certificate(cred_dict)
        firebase_admin.initialize_app(cred, {
            "databaseURL": os.getenv("DATABASE_URL")
        })

    return db