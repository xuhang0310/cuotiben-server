from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.schemas.conversation import PaginatedMembers
from app.services.conversation import get_conversation_members
from datetime import datetime
import json

router = APIRouter(prefix="", tags=["prompt-generator"])


@router.get("/{conversation_id}/conversion-prompt", response_model=dict)
def get_conversion_prompt(conversation_id: str, db: Session = Depends(get_db)):
    """
    获取对话转换的提示词
    :param conversation_id: 会话ID
    :param db: 数据库会话
    :return: 包含提示词的字典
    """
    # 获取会话成员列表
    members_result = read_conversation_members(conversation_id, db)
    
    # 构建成员列表JSON字符串
    members_list = []
    for member in members_result.data:
        member_dict = {
            "id": member.user_id,
            "name": member.member_name or f"用户{member.user_id}",
            "role": "成员"
        }
        members_list.append(member_dict)
    
    # 当前时间
    current_time = datetime.now()
    current_time_str = current_time.strftime("%H:%M")
    current_iso_time = current_time.strftime("%Y-%m-%dT%H:%M:%S")
    
    # 构建提示词
    prompt = f"""### 任务描述
请将提供的多人对话文本，按照以下规则转换为严格的JSON数组格式，数组中每个元素对应一条对话内容。

### 核心规则
1. **JSON模板（单条对话）**：
{{
    "conversation_id": "{conversation_id}",  // 固定值，所有条目保持不变
    "user_id": 12,                       // 替换为对应说话人的id（见成员列表）
    "content": "1111",                   // 替换为纯对话内容（仅保留文字，忽略心理/表情描述）
    "message_type": "text",              // 固定值
    "content_format": "plain",           // 固定值
    "is_deleted": 0,                     // 固定值
    "message_metadata": {{}},              // 固定格式，保持空对象
    "display_time": "{current_time_str}",             // 替换为当前系统时间，仅精确到分钟（格式：HH:MM）
    "created_at": "{current_iso_time}", // 可替换为当前时间，格式保持 ISO 8601（YYYY-MM-DDTHH:MM:SS）
    "updated_at": "{current_iso_time}", // 与created_at保持一致
    "member_name": null,                 // 替换为对应说话人的name（见成员列表）
    "avatar": null                       // 固定值null
}}

2. **成员列表（用于匹配user_id和member_name）**：
{json.dumps(members_list, ensure_ascii=False, indent=2)}

3. **格式要求**：
- 最终输出为JSON数组，数组内每个元素是单条对话的JSON对象；
- 严格遵循JSON语法（引号、逗号、花括号/方括号使用正确，无多余空格/换行）；
- `display_time` 仅保留小时和分钟（如：14:35），不显示秒；
- 仅提取纯对话内容，完全忽略心理活动、表情描述、动作描写等非对话文本；
- 每个说话人的内容对应一条JSON对象，`user_id`和`member_name`必须与成员列表精准匹配。

### 输出要求
请直接输出最终的JSON数组，无需额外解释、说明或备注。"""

    return {"prompt": prompt}


def read_conversation_members(conversation_id: str, db: Session):
    """
    获取会话成员列表的辅助函数
    """
    from app.models.conversation import ConversationMember
    from app.models.historical_figure import HistoricalFigure
    from app.schemas.conversation import ConversationMemberWithUserInfo

    # 使用JOIN查询获取成员的名称和头像信息
    query = db.query(
        ConversationMember,
        HistoricalFigure.name.label('member_name'),
        HistoricalFigure.avatar.label('avatar')
    ).outerjoin(
        HistoricalFigure, ConversationMember.user_id == HistoricalFigure.id
    ).filter(ConversationMember.conversation_id == conversation_id)

    total_query = db.query(ConversationMember).filter(ConversationMember.conversation_id == conversation_id)
    total = total_query.count()

    results = query.limit(100).all()  # 限制返回数量

    # 将结果转换为包含额外字段的对象
    members = []
    for member, member_name, avatar in results:
        member_response = ConversationMemberWithUserInfo(
            conversation_id=member.conversation_id,
            user_id=member.user_id,
            user_role=member.user_role,
            id=member.id,
            joined_at=member.joined_at,
            member_name=member_name,
            avatar=avatar
        )
        members.append(member_response)

    return PaginatedMembers(
        total=total,
        page=1,
        size=len(members),
        pages=1,
        data=members
    )