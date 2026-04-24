from fastapi import APIRouter, UploadFile, File, Depends, Form, HTTPException
from database.firebase import get_db
from datetime import datetime
from .auth import verify_token
from dotenv import load_dotenv
import os
import requests
import traceback
from supabase import create_client, Client

load_dotenv()

# --- ENV ---
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
MODEL_API_URL = os.getenv("APIPATH")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise Exception("❌ Supabase config missing")

if not MODEL_API_URL:
    raise Exception("❌ MODEL_API_URL missing")

# --- Clients ---
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
BUCKET_NAME = os.getenv("BUCKETS_NAME")

db = get_db()

router = APIRouter(prefix="/predict", tags=["predict"])


@router.post("/")
async def predict(
    file: UploadFile = File(...),
    model_name: str = Form(...),
    user=Depends(verify_token),
):
    # ✅ Validate user
    if not user or "uid" not in user:
        raise HTTPException(status_code=401, detail="Invalid user")

    try:
        print("🚀 START PREDICT")
        print("USER:", user)
        print("MODEL_API_URL:", MODEL_API_URL)

        # --- STEP 1: READ FILE ---
        file_content = await file.read()

        if not file_content:
            raise HTTPException(status_code=400, detail="Empty file")

        file_extension = os.path.splitext(file.filename)[1] or ".jpg"

        unique_filename = f"{user['uid']}/{int(datetime.now().timestamp())}{file_extension}"
        print("FILENAME:", unique_filename)



        # --- STEP 3: CALL MODEL API ---
        try:
            files = {
                "file": (file.filename, file_content, file.content_type)
            }
            data = {"model_name": model_name}

            response = requests.post(
                f"{MODEL_API_URL}/predict",  
                files=files,
                data=data,
                timeout=20
            )
            print("MODEL_API_URL:", MODEL_API_URL)
            print("MODEL STATUS:", response.status_code)
            print("RESPONSE:", response.text)
            

            if not response.ok:
                print("❌ Model API Error:", response.text)
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Model API error: {response.text}"
                )

            result = response.json()

        except requests.Timeout:
            raise HTTPException(status_code=504, detail="Model API timeout")
        except Exception as e:
            print("❌ Model API Crash:", e)
            raise HTTPException(status_code=500, detail=f"Model API crash: {str(e)}")
        # --- STEP 2: UPLOAD TO SUPABASE ---
        try:
            supabase.storage.from_(BUCKET_NAME).upload(
                path=unique_filename,
                file=file_content,
                file_options={"content-type": file.content_type}
            )

            image_url = supabase.storage.from_(BUCKET_NAME).get_public_url(unique_filename)

        except Exception as e:
            print("❌ Supabase Error:", e)
            raise HTTPException(status_code=500, detail=f"Supabase Upload Error: {str(e)}")
        
        # --- STEP 4: SAVE TO FIREBASE ---
        try:
            user_ref = db.reference(f"/users/{user['uid']}")
            user_data = user_ref.get()

            if user_data:
                ref = db.reference(f"/users/{user['uid']}/results")
                new_ref = ref.push()
                new_ref.set({
                    "prediction": result,
                    "image_url": image_url,
                    "file_path": unique_filename,
                    "created_at": datetime.now().isoformat(),
                    "model_name": model_name
                })
            else:
                print("⚠️ User not found in Firebase, skip saving")

        except Exception as e:
            print("❌ Firebase Error:", e)

        # --- SUCCESS ---
        return {
            "result": result,
            # "image_url": image_url,
            "model_name": model_name
        }

    except HTTPException:
        raise

    except Exception as e:
        print("🔥 UNEXPECTED ERROR")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))