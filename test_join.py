from sqlalchemy import create_engine, text
from urllib.parse import quote_plus
from app.core.config import settings

# 创建数据库引擎 - 使用quote_plus正确处理特殊字符
DB_PASSWORD = quote_plus(settings.DB_PASSWORD)
SQLALCHEMY_DATABASE_URL = f"mysql+mysqlconnector://{settings.DB_USER}:{DB_PASSWORD}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"

engine = create_engine(SQLALCHEMY_DATABASE_URL)

with engine.connect() as conn:
    # 执行JOIN查询
    result = conn.execute(text("""
        SELECT cm.id, cm.conversation_id, cm.user_id, cm.user_role, cm.joined_at,
               hf.name as member_name, hf.avatar
        FROM conversation_members cm
        LEFT JOIN historical_figures hf ON cm.user_id = hf.id
        WHERE cm.conversation_id = 'test_conversation'
        LIMIT 10
    """))
    
    print("JOIN查询结果:")
    for row in result:
        print(f"  ID: {row[0]}, Conv: {row[1]}, User: {row[2]}, Role: {row[3]}, Joined: {row[4]}, Name: {row[5]}, Avatar: {row[6]}")