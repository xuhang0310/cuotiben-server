from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import auth, users, questions, practice, statistics, settings, historical_figures
from app.database.session import engine, Base
from app.core.config import settings as app_settings

# 创建数据库表
Base.metadata.create_all(bind=engine)

# 创建FastAPI应用
app = FastAPI(
    title="错题本系统API",
    description="错题本系统的后端API",
    version="1.0.0"
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应该指定具体的域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 包含路由
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(questions.router, prefix="/api/questions", tags=["questions"])
app.include_router(practice.router, prefix="/api/practice", tags=["practice"])
app.include_router(statistics.router, prefix="/api/statistics", tags=["statistics"])
app.include_router(settings.router, prefix="/api/settings", tags=["settings"])
app.include_router(historical_figures.router, prefix="/api/historical-figures", tags=["historical-figures"])

@app.get("/")
def read_root():
    return {"message": "Welcome to the cuotiben backend API"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}