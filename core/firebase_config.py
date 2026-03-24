import firebase_admin
from firebase_admin import credentials, db

cred = credentials.Certificate("serviceAccountKey.json")

firebase_admin.initialize_app(cred, {
    "databaseURL": "https://senior-b3690-default-rtdb.asia-southeast1.firebasedatabase.app"
})
