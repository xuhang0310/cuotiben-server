# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python FastAPI backend for "错题本系统" (Error Notebook System), an AI-powered learning platform. The core feature is an AI group chat system where multiple AI personalities with distinct characteristics participate in group conversations.

## Common Commands

### Development

```bash
# Start the server (development with hot reload)
python run.py

# Or use the startup script (creates venv, installs deps, runs in background)
./start.sh

# Initialize database tables
python init_db.py

# View logs when running with start.sh
tail -f logs/app_*.log
```

### Testing

```bash
# Run API tests
python test_complete_api.py

# Run Qwen AI API tests
python test_qwen_api.py

# Run AI group chat improvement tests
python test_ai_group_chat_improvements.py
```

### Environment Setup

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with database credentials and API keys
```

## Architecture

### Tech Stack
- **Framework**: FastAPI with async support
- **Database**: MySQL with SQLAlchemy ORM
- **Authentication**: JWT-based
- **AI Integration**: Alibaba Cloud Qwen API via `ai_model_service.py`

### Directory Structure

```
app/
├── api/              # FastAPI route handlers
│   ├── ai_group_chat.py    # Core AI group chat endpoints
│   ├── auth.py             # JWT authentication
│   └── ...
├── services/         # Business logic layer
│   ├── ai_group_chat_service.py   # Main AI chat orchestration
│   ├── ai_model_service.py        # AI API integration
│   ├── ai_character_service.py    # Personality/role management
│   ├── ai_context_manager.py      # Context building for prompts
│   └── ai_relevance_detector.py   # Smart trigger detection
├── models/           # SQLAlchemy database models
├── schemas/          # Pydantic validation models
├── core/             # Config and security utilities
└── database/         # Database session management
```

### Key Architectural Patterns

**AI Group Chat System** (`app/services/ai_group_chat_service.py`):
The core service orchestrates AI responses by:
1. Building enhanced context that distinguishes Self/Other AI/Human messages (`ai_context_manager.py`)
2. Creating role-aware prompts based on AI personality and stance
3. Calling AI models via `ai_model_service.py`
4. Post-processing responses for naturalness
5. Detecting character drift via `ai_character_service.py`

**Context Management** (`app/services/ai_context_manager.py`):
- `build_enhanced_context()`: Segments conversation history by participant type
- `create_role_aware_prompt()`: Generates prompts that reinforce AI identity
- Messages are categorized as: self_history, other_ai_interactions, human_interactions

**Smart Triggering** (`app/services/ai_relevance_detector.py`):
AI members only respond when:
- Directly mentioned by name
- Topic is relevant to their expertise
- Random organic participation (weighted by personality)

**Character Consistency** (`app/services/ai_character_service.py`):
- `CharacterDriftPrevention`: Detects when AI responses deviate from defined personality
- `ConsistencyReinforcement`: Adds identity reinforcement to prompts
- Personalities defined in `AiGroupMember.personality` field (max 500 chars)

### Database Models (Key)

- `AiChatGroup`: Chat group container
- `AiGroupMember`: AI participant with personality/stance config
- `AiMessage`: Chat messages (both human and AI)
- `AiModel`: AI model configuration (endpoint, API key, parameters)
- `User`: Human users with JWT authentication

### API Flow

1. Human sends message → `POST /api/ai-group-chat/{group_id}/messages`
2. System stores message, triggers relevance detection
3. For each AI member: `SmartTriggerDetector` decides if should respond
4. If triggered: `AiGroupChatService.generate_response()` builds context + calls AI
5. AI response stored and returned via SSE/WebSocket or polling

### Configuration

Environment variables (`.env`):
- `DB_HOST`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`: MySQL connection
- `SECRET_KEY`, `ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES`: JWT settings
- `ALIBABA_CLOUD_API_KEY`: AI model API access
- `HOST`, `PORT`: Server binding

## Development Rules (from RULES.md)

- **Naming**: snake_case for functions/variables, PascalCase for classes
- **Function length**: Max 50 lines, classes max 300 lines
- **Type hints**: Required for all function signatures
- **Imports**: stdlib > third-party > local (separate groups with blank lines)
- **API design**: RESTful, max 3 path levels, use HTTP methods for actions
- **AI personality**: Max 500 chars, specific traits ("逻辑严谨" not "聪明")
- **Response time targets**: API <500ms (95th percentile), AI generation <10s

## Important Notes

- Python 3.13 compatible dependencies are specified in `requirements.txt`
- The app uses Pydantic v2 with `pydantic-settings` for config
- Database tables are auto-created on startup via `Base.metadata.create_all()`
- Static files served from `/static` route (mounted at `app/` directory)
- API documentation available at `/docs` (Swagger) and `/redoc` (ReDoc) when running
