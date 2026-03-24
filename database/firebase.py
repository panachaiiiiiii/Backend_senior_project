import firebase_admin
from firebase_admin import credentials, db
import os
import json

def get_db():
    if not firebase_admin._apps:
        firebase_key = os.getenv("FIREBASE_KEY")

        if not firebase_key:
            raise ValueError("FIREBASE_KEY not found in environment")

        cred_dict = json.loads(firebase_key)

        cred = credentials.Certificate(cred_dict)

        firebase_admin.initialize_app(cred, {
            "databaseURL": os.getenv("DATABASE_URL")
        })

    return db