from fastapi import APIRouter, UploadFile, File, Depends, Form, HTTPException
from PIL import Image
from database.firebase import get_db
from datetime import datetime
from .auth import verify_token
from dotenv import load_dotenv
import os

import requests
db = get_db()

load_dotenv()
MODEL_API_URL = os.getenv("APIPATH")

router = APIRouter(prefix="/predict", tags=["predict"])



@router.post("/")
async def predict(
    file: UploadFile = File(...),
    model_name: str = Form(...),
    user=Depends(verify_token),  # เปิดถ้าใช้ระบบ auth
):
   
    # ✅ reset pointer ของไฟล์
    file.file.seek(0)

    # ✅ เตรียมส่งไป Model API
    files = {"file": (file.filename, file.file, file.content_type)}
    data = {
        "model_name": model_name  # 🔥 ส่งต่อไป model API
    }
    try:
        response = requests.post(
            MODEL_API_URL+"/predict",
            files=files,
            data=data,
            timeout=15  # เพิ่ม timeout เผื่อ model ใช้เวลานาน
        )
        if not response.ok:
            try:
                error_json = response.json()
                detail = error_json.get("detail") or error_json.get("error")
            except ValueError:
                detail = response.text

            raise HTTPException(
                status_code=response.status_code,
                detail=f"Model API error: {detail}"
            )
        try:
            result = response.json()
        except ValueError:
            raise HTTPException(
                status_code=502,
                detail=f"Invalid JSON from Model API: {response.text}"
            )
        user_ref = db.reference(f"/users/{user['uid']}")
        user_data = user_ref.get()

        if user_data:
            ref = db.reference(f"/users/{user['uid']}/results")
            new_ref = ref.push()
            new_ref.set({
                "prediction": result,
                "created_at": datetime.now().isoformat(),
            })
        return {
            "result": result,
            "model_name": result.get("model_name") or model_name
        }

    except requests.Timeout:
        raise HTTPException(status_code=504, detail="Model API timeout")

    except requests.ConnectionError:
        raise HTTPException(status_code=502, detail="Cannot connect to Model API")

    except HTTPException as e:
        raise HTTPException(
            status_code=e.status_code,
            detail=f"[Predict API] {e.detail}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {str(e)}"
        )

    # ✅ บันทึก Firebase



    
    # "model": model_name