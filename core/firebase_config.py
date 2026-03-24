import firebase_admin
from firebase_admin import credentials, db
import os
import json

firebase_key = os.getenv("FIREBASE_KEY")

if not firebase_key:
    raise ValueError("FIREBASE_KEY is missing")

cred_dict = json.loads(firebase_key)

cred = credentials.Certificate(cred_dict)

firebase_admin.initialize_app(cred, {
    "databaseURL": "https://senior-b3690-default-rtdb.asia-southeast1.firebasedatabase.app"
})