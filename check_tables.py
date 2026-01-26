from sqlalchemy import create_engine, text
from urllib.parse import quote_plus
from app.core.config import settings

# 创建数据库引擎 - 使用quote_plus正确处理特殊字符
DB_PASSWORD = quote_plus(settings.DB_PASSWORD)
SQLALCHEMY_DATABASE_URL = f"mysql+mysqlconnector://{settings.DB_USER}:{DB_PASSWORD}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"

engine = create_engine(SQLALCHEMY_DATABASE_URL)

with engine.connect() as conn:
    # 查询chat_messages表的列信息
    result = conn.execute(text("DESCRIBE chat_messages"))
    columns = result.fetchall()
    
    print("chat_messages表结构:")
    for col in columns:
        print(f"  {col[0]} - {col[1]} - {col[2]} - {col[3]} - {col[4]} - {col[5]}")
    
    print("\nconversation_members表结构:")
    result = conn.execute(text("DESCRIBE conversation_members"))
    columns = result.fetchall()
    for col in columns:
        print(f"  {col[0]} - {col[1]} - {col[2]} - {col[3]} - {col[4]} - {col[5]}")
    
    print("\nconversations表结构:")
    result = conn.execute(text("DESCRIBE conversations"))
    columns = result.fetchall()
    for col in columns:
        print(f"  {col[0]} - {col[1]} - {col[2]} - {col[3]} - {col[4]} - {col[5]}")