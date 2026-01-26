from app.schemas.conversation import ConversationMemberWithUserInfo
from datetime import datetime

# 测试创建对象
member_data = {
    'id': 6,
    'conversation_id': 'test_conversation',
    'user_id': 1,
    'user_role': 'owner',
    'joined_at': datetime.fromisoformat('2026-01-26T05:38:50'),
    'member_name': '始皇帝嬴政',
    'avatar': '/images/qinshihuang.png'
}

member = ConversationMemberWithUserInfo(**member_data)
print("Created member object:")
print(f"  id: {member.id}")
print(f"  conversation_id: {member.conversation_id}")
print(f"  user_id: {member.user_id}")
print(f"  user_role: {member.user_role}")
print(f"  joined_at: {member.joined_at}")
print(f"  member_name: {member.member_name}")
print(f"  avatar: {member.avatar}")

# 测试序列化
import json
from datetime import datetime
from decimal import Decimal

def json_serializer(obj):
    """自定义JSON序列化器"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, Decimal):
        return float(obj)
    raise TypeError(f"Object of type {obj.__class__.__name__} is not JSON serializable")

serialized = member.model_dump()
print("\nSerialized object:")
print(json.dumps(serialized, default=json_serializer, ensure_ascii=False, indent=2))