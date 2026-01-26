from sqlalchemy import create_engine, text
from urllib.parse import quote_plus
from app.core.config import settings

# 创建数据库引擎 - 使用quote_plus正确处理特殊字符
DB_PASSWORD = quote_plus(settings.DB_PASSWORD)
SQLALCHEMY_DATABASE_URL = f"mysql+mysqlconnector://{settings.DB_USER}:{DB_PASSWORD}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"

engine = create_engine(SQLALCHEMY_DATABASE_URL)

with engine.connect() as conn:
    # 查询conversation_members表中的用户ID
    result = conn.execute(text("SELECT id, conversation_id, user_id FROM conversation_members LIMIT 10"))
    print("conversation_members表中的记录:")
    for row in result:
        print(f"  ID: {row[0]}, Conversation: {row[1]}, User ID: {row[2]}")
    
    print("\nhistorical_figures表中的记录:")
    result = conn.execute(text("SELECT id, name, avatar FROM historical_figures LIMIT 10"))
    for row in result:
        print(f"  ID: {row[0]}, Name: {row[1]}, Avatar: {row[2]}")