from fastapi import APIRouter
from dotenv import load_dotenv
from database.firebase import get_db
import os
import requests

load_dotenv()
MODEL_API_URL = os.getenv("APIPATH")

router = APIRouter()
def get_database():
    return get_db()

MODEL_STATUS = {
    "modelA": True,
    "modelB": False,
}
@router.get("/models")
def get_models():
    try:
        # 🔹 ดึง model จาก Model API
        response = requests.get(f"{MODEL_API_URL}/models", timeout=10)
        response.raise_for_status()
        result = response.json()

        model_list = result.get("models", [])
        names = [m["name"] for m in model_list]

        # 🔹 ดึงสถานะจาก Firebase
        ref = db.reference("/models")
        db_data = ref.get() or {}

        # 🔹 sync: เพิ่ม model ใหม่เข้า DB
        updates = {}
        for name in names:
            if name not in db_data:
                updates[name] = True  # default = เปิด

        if updates:
            ref.update(updates)
            db_data.update(updates)  # sync local

        # 🔹 รวม name + enabled
        models = [
            {
                "name": name,
                "enabled": db_data.get(name, True)
            }
            for name in names
        ]

        return {
            "models": models,
            "status": 200
        }

    except requests.RequestException:
        # 🔹 fallback ใช้ DB อย่างเดียว
        ref = db.reference("/models")
        db_data = ref.get() or {}

        return {
            "models": [
                {"name": name, "enabled": status}
                for name, status in db_data.items()
            ],
            "status": 200
        }
    
from pydantic import BaseModel

class ModelToggle(BaseModel):
    name: str
    enabled: bool

@router.put("/models/toggle")
def toggle_model(data: ModelToggle):
    ref = db.reference("/models")
    db_data = ref.get() or {}

    # ✅ เช็คว่ามี model นี้ใน DB ไหม
    if data.name not in db_data:
        return {
            "status": 400,
            "detail": "Model not found"
        }

    # ✅ update ค่า
    ref.child(data.name).set(data.enabled)

    return {
        "status": 200,
        "data": {
            "name": data.name,
            "enabled": data.enabled
        }
    }