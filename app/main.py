from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.api import historical_figures, conversations
from app.api import upload, prompt_generator
from app.api import qwen_ai
from app.api import ai_chat
from app.api import auth
from app.database.session import engine, Base
from app.core.config import settings as app_settings

# 创建数据库表
Base.metadata.create_all(bind=engine)

# 创建FastAPI应用
app = FastAPI(
    title="自媒体营销系统API",
    description="自媒体营销系统的后端API",
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
app.include_router(historical_figures.router, prefix="/api/historical-figures", tags=["historical-figures"])
app.include_router(conversations.router, prefix="/api/chat", tags=["conversations"])
app.include_router(upload.router, prefix="/api", tags=["upload"])
app.include_router(prompt_generator.router, prefix="/api/prompt", tags=["prompt-generator"])
app.include_router(qwen_ai.router, prefix="/api/qwen", tags=["qwen-ai"])
app.include_router(ai_chat.router, prefix="/api", tags=["ai-chat"])
app.include_router(auth.router, prefix="/api", tags=["authentication"])

# 挂载静态文件目录，用于访问上传的图片
app.mount("/static", StaticFiles(directory="app"), name="static")

@app.get("/")
def read_root():
    return {"message": "Welcome to the cuotiben backend API"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}