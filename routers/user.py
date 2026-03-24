from fastapi import APIRouter, Depends, HTTPException
from database.firebase import get_db
from pydantic import BaseModel
from datetime import date
from .auth import create_token, verify_token
from typing import Optional

router = APIRouter()
def get_database():
    return get_db()


class UpdateUser(BaseModel):
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    sex: Optional[str] = None
    birthday: Optional[str] = None
    role: Optional[str] = None

class Userinfo(BaseModel):
    first_name: str
    last_name: str
    sex: str
    birthday: date



# =========================
# GET HISTORY
# =========================
@router.get("/history")
def getdata(user=Depends(verify_token)):
    ref = db.reference(f"/users/{user['uid']}/results")
    data = ref.get()
    print("UID : ",user['uid'])
    print("data is ",data)
    return {
        "data":data,
        "status": 200
    }


# =========================
# GET USER PROFILE
# =========================
@router.get("/setting")
def getdata(user=Depends(verify_token)):

    ref = db.reference(f"/users/{user['uid']}")
    data = ref.get()

    if data:
        return {
            "user": data,
            "status": 202
        }

    return {"status": 400}

# =========================
# GUEST LOGIN
# =========================
@router.get("/guest")
def LoginGuest():

    token = create_token({
        "uid": "Guest"
    })

    return {
        "token": token,
        "status": 200
    }

# =========================
# UPDATE OWN PROFILE
# =========================
@router.put("/setting")
def update_profile(
    data: UpdateUser,
    user=Depends(verify_token)
):

    uid = user["uid"]

    ref = db.reference(f"/users/{uid}")

    if not ref.get():
        raise HTTPException(status_code=404, detail="User not found")

    update_data = data.dict(exclude_unset=True)

    if update_data:
        ref.update(update_data)

    return {
        "status": 201,
        "detail": "updated"
    }