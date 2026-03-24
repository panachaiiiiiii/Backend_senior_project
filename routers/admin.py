from fastapi import APIRouter, HTTPException
from firebase_admin import auth
from database.firebase import get_db
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

router = APIRouter()
db = get_db()


class UpdateUser(BaseModel):
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    sex: Optional[str] = None
    birthday: Optional[str] = None
    role: Optional[str] = None


# =========================
# DELETE USER
# =========================
@router.delete("/user/{uid}")
def delete_user(uid: str):
    try:
        auth.delete_user(uid)

        ref = db.reference(f"/users/{uid}")
        ref.delete()

        return {
            "status": 200,
            "detail": "User deleted"
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# =========================
# UPDATE USER (ADMIN)
# =========================
@router.put("/user/{uid}")
def update_user(uid: str, body: UpdateUser):

    ref = db.reference(f"/users/{uid}")
    data = ref.get()

    if not data:
        return {
            "status": 404,
            "message": "User not found"
        }

    update_data = body.dict(exclude_unset=True)

    if update_data:
        ref.update(update_data)

    return {
        "status": 200,
        "message": "updated"
    }


# =========================
# GET HISTORY USERS
# =========================
@router.get("/admin/history/{uid}")
def getdata(uid: str):
    ref = db.reference(f"/users/{uid}/results")
    data = ref.get()

    return {
        "data": data,
        "status": 200
    }


# =========================
# GET ALL USERS
# =========================
@router.get("/user")
def get_all_users():

    ref = db.reference("/users")
    data = ref.get()

    if not data:
        return {
            "status": 200,
            "users": []
        }

    users = []

    for uid, value in data.items():
        users.append({
            "uid": uid,
            "email": value.get("email", ""),
            "name": value.get("first_name", ""),
            "lastname": value.get("last_name", ""),
            "gender": value.get("sex", ""),
            "birthday": value.get("birthday", ""),
            "login_from": value.get("login_from", ""),
            "role": value.get("role", "user")
        })

    return {
        "status": 200,
        "users": users
    }


# =========================
# CALCULATE AGE
# =========================
def calculate_age(birthday):
    try:
        birth = datetime.strptime(birthday, "%Y-%m-%d")
        today = datetime.today()

        age = today.year - birth.year
        if (today.month, today.day) < (birth.month, birth.day):
            age -= 1

        return age
    except:
        return 0


# =========================
# DASHBOARD
# =========================
@router.get("/userstate")
def dashboard_stats():

    ref = db.reference("/users")
    users = ref.get()

    if not users:
        return {
            "total_users": 0,
            "avg_age": 0,
            "gender": {"male": 0, "female": 0},
            "disease_frequency": [],
            "model_distribution": [],
            "total_scans": 0
        }

    total_users = 0
    total_age = 0
    age_count = 0
    male = 0
    female = 0
    total_scans = 0

    disease_count = {}

    # 🔥 ใหม่
    model_count = {}
    model_prediction_map = {}

    for uid, user in users.items():
        total_users += 1

        # -------- AGE --------
        birthday = user.get("birthday")
        if birthday:
            age = calculate_age(birthday)
            if age > 0:
                total_age += age
                age_count += 1

        # -------- GENDER --------
        sex = user.get("sex", "").lower()
        if sex == "male":
            male += 1
        elif sex == "female":
            female += 1

        # -------- RESULTS --------
        results = user.get("results", {})

        for rid, result in results.items():
            total_scans += 1
            resultss = result.get("prediction")
            prediction = resultss.get("result", {})
            model = resultss.get("model")

            if not prediction:
                continue

            # 🔥 disease ที่ prob สูงสุด
            disease = max(prediction, key=prediction.get)

            # -------- disease frequency --------
            disease_count[disease] = disease_count.get(disease, 0) + 1

            # -------- model logic --------
            if model:
                # นับ model
                model_count[model] = model_count.get(model, 0) + 1

                # เตรียม dict
                if model not in model_prediction_map:
                    model_prediction_map[model] = {}

                # นับ disease ต่อ model
                model_prediction_map[model][disease] = (
                    model_prediction_map[model].get(disease, 0) + 1
                )

    avg_age = round(total_age / age_count) if age_count else 0

    # -------- disease frequency --------
    disease_frequency = sorted(
        [{"disease": k, "count": v} for k, v in disease_count.items()],
        key=lambda x: x["count"],
        reverse=True
    )

    # -------- 🔥 model distribution ใหม่ --------
    model_distribution = sorted(
        [
            {
                "model": model,
                "count": count,
                "prediction": model_prediction_map.get(model, {})
            }
            for model, count in model_count.items()
        ],
        key=lambda x: x["count"],
        reverse=True
    )

    return {
        "total_users": total_users,
        "avg_age": avg_age,
        "gender": {
            "male": male,
            "female": female
        },
        "disease_frequency": disease_frequency,
        "model_distribution": model_distribution,  # ✅ ใหม่
        "total_scans": total_scans
    }