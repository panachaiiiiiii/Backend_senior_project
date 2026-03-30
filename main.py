from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from routers import user, auth, predict,admin,model

app = FastAPI()
# ดึง environment variable
origins = os.getenv("FRONTEND_URLS", "")
# แปลงเป็น list
# allow_origins = [
#     "http://localhost:5173",
#     "http://127.0.0.1:5173",
#     "http://localhost:3000"
# ]
allow_origins = [url.strip() for url in origins.split(",") if url.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://senior-iota.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "FastAPI + Firebase RTDB is working"}

app.include_router(user.router)
app.include_router(auth.router)
app.include_router(predict.router)
app.include_router(admin.router)
app.include_router(model.router)
