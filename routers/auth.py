from fastapi import APIRouter, Request
from database.firebase import get_db
from jose import jwt,JWTError
from datetime import datetime, timedelta,date
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from firebase_admin.auth import create_user
import os
from firebase_admin.auth import verify_id_token
from pydantic import BaseModel
from services.google_auth import verify_google_token
from passlib.context import CryptContext
load_dotenv()

router = APIRouter()
db = get_db()
security = HTTPBearer()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str):
    return pwd_context.hash(password)
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


class Userinfo(BaseModel):
    first_name : str
    last_name : str
    sex : str
    birthday : date
class Token(BaseModel):
    token:str

class UserRegister(BaseModel):
    email : str
    password : str


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        print(payload)
        return payload
    except JWTError as e:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
def create_token(data: dict):
    payload = data.copy()
    payload["iat"] = datetime.utcnow()
    payload["exp"] = datetime.utcnow() + timedelta(hours=1)

    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

    return token


@router.post("/register")
def register(UserRegister: UserRegister):
    try:
        user = create_user(
            email=UserRegister.email,
            password=UserRegister.password
        )

        uid = user.uid

        # เก็บข้อมูลผู้ใช้ใน Realtime DB
        user_ref = db.reference(f"users/{uid}")
        role = "user"

        user_ref.set({
            "email": user.email,
            "role": role,
            "login_from": "register"
        })

        token = create_token({
            "uid": uid,
            "role": role,
            "login": True
        })
        return {
            "status": 201,
            "token": token
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/login/google")
async def login(request: Request):

    body = await request.json()
    access_token = body.get("access_token")

    user_info = verify_google_token(access_token)

    uid = user_info["sub"]

    user_ref = db.reference(f"users/{uid}")
    user = user_ref.get()

    token = create_token({"uid": uid, "login": True})

    if not user:
        user_ref.set({
            "email": user_info["email"],
            "role": "user",
            "login_from": "google",
        })

        return {
            "token": token,
            "status": 201
        }

    if user and "birthday" in user and "sex" in user:
        return {
            "token": token,
            "status": 200,
            "user": user
        }

    return {
        "token": token,
        "status": 201
    }
@router.post("/login")
def login(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        print("🔥 HIT LOGIN")
        token = credentials.credentials
        if not credentials:
            raise HTTPException(status_code=401, detail="No credentials")
        print("TOKEN LENGTH:", len(token))

        decoded = verify_id_token(token)
        print("DECODED:", decoded)

        uid = decoded.get("uid") or decoded.get("user_id")

        ref = db.reference(f"users/{uid}")
        user = ref.get()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        tokens = create_token({"uid": uid,"login":True})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        return {
            "status": 200,
            "token": tokens,
            "user": user
        }

    except Exception as e:
        print("VERIFY ERROR:", e)
        raise HTTPException(status_code=401, detail=str(e))


@router.put("/setupprofile")
def setupuser(
    Userinfo: Userinfo,
    user = Depends(verify_token)
):
    print(user)

    ref = db.reference(f"/users/{user['uid']}")

    if ref.get():
        ref.update({
            "first_name": Userinfo.first_name,
            "last_name": Userinfo.last_name,
            "birthday": Userinfo.birthday.isoformat(),
            "sex": Userinfo.sex
        })
        return {"status": 202}

    raise HTTPException(status_code=404, detail="User not found")
