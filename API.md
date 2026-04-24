# AIU API Documentation

**Base URL:** `https://yourdomain.com/api/v1/`  
**Auth:** Bearer JWT — `Authorization: Bearer <access_token>`  
**Format:** All requests/responses are `application/json`

---

## Authentication

### Register
`POST /auth/register/`

```json
{
  "email": "user@example.com",
  "password": "SecurePassword123!",
  "first_name": "Alex",
  "last_name": "Smith",
  "timezone": "America/New_York",
  "goals": ["Improve focus", "Build exercise habit"]
}
```

**Response 201:**
```json
{
  "status": "success",
  "tokens": { "access": "eyJ...", "refresh": "eyJ..." },
  "user": { "id": "uuid", "email": "...", "profile": {...} }
}
```

### Login
`POST /auth/login/`

```json
{ "email": "user@example.com", "password": "SecurePassword123!" }
```

**Response 200:** `{ "access": "eyJ...", "refresh": "eyJ..." }`

### Refresh Token
`POST /auth/token/refresh/`

```json
{ "refresh": "eyJ..." }
```

### Logout
`POST /auth/logout/`  *(requires auth)*

```json
{ "refresh": "eyJ..." }
```

---

## User

### Get Current User
`GET /users/me/`

**Response:**
```json
{
  "status": "success",
  "data": {
    "id": "uuid",
    "email": "user@example.com",
    "first_name": "Alex",
    "role": "user",
    "profile": {
      "coach_mode": "friendly",
      "timezone": "UTC",
      "goals": [],
      "behavior_patterns": {},
      "productivity_windows": [9, 10, 14],
      "onboarding_completed": false
    }
  }
}
```

### Update Profile
`PATCH /users/me/`

Accepted fields: `first_name`, `last_name`, `coach_mode`, `timezone`, `language`, `goals`, `onboarding_completed`

### Change Password
`POST /users/change-password/`

```json
{ "old_password": "...", "new_password": "NewSecurePassword123!" }
```

---

## AI Chat

### Send Message
`POST /ai/chat/`

```json
{
  "message": "What should I focus on today?",
  "conversation_id": "uuid (optional — omit to start new)",
  "coach_mode": "friendly | mentor | strict | analytical",
  "stream": false,
  "context": {
    "mood": "anxious",
    "current_habits": ["morning run", "meditation"]
  }
}
```

**Response (non-streaming):**
```json
{
  "status": "success",
  "data": {
    "content": "Based on your patterns, I suggest...",
    "conversation_id": "uuid",
    "message_id": "uuid",
    "tokens_used": 450,
    "model": "gpt-4o",
    "retrieved_memories": 3,
    "latency_ms": 892.5
  }
}
```

**Streaming (`stream: true`):**  
Returns `text/event-stream`. Each chunk: `data: <text>\n\n`  
Final chunk: `data: [DONE]\n\n`

**Rate limit:** 60 requests/hour per user

### List Conversations
`GET /ai/conversations/`

### Get Conversation + Messages
`GET /ai/conversations/{id}/`

### Archive Conversation
`DELETE /ai/conversations/{id}/`

---

## Habits

### List Habits
`GET /habits/`

### Today's Habits (with completion status)
`GET /habits/today/`

**Response:**
```json
{
  "status": "success",
  "date": "2024-07-15",
  "results": [
    {
      "id": "uuid",
      "name": "Morning meditation",
      "category": "mindfulness",
      "current_streak": 12,
      "longest_streak": 30,
      "completion_rate_7d": 85.7,
      "completed_today": false
    }
  ]
}
```

### Create Habit
`POST /habits/`

```json
{
  "name": "Morning meditation",
  "category": "mindfulness",
  "description": "10 minutes mindfulness meditation",
  "frequency": "daily"
}
```

### Log Habit Completion
`POST /habits/{id}/log/`

```json
{
  "log_date": "2024-07-15",
  "notes": "Felt great today",
  "mood_rating": 4,
  "difficulty_rating": 2
}
```

**Response:**
```json
{
  "status": "success",
  "created": true,
  "current_streak": 13,
  "log": { "id": "...", "log_date": "...", ... }
}
```

### Habit History
`GET /habits/{id}/history/?days=30`

---

## Analytics

### Dashboard Stats
`GET /analytics/dashboard/`

**Response:**
```json
{
  "status": "success",
  "data": {
    "habits": {
      "active_count": 5,
      "completed_today": 3,
      "completion_30d": 82,
      "top_streak": 14
    },
    "conversations": {
      "total": 47,
      "last_7_days": 12,
      "total_messages": 284,
      "avg_sentiment": 0.23
    },
    "insights": {
      "total": 18,
      "breakdown": [
        { "insight_type": "behavior", "count": 7 }
      ]
    },
    "activity": {
      "heatmap_by_hour": { "9": 15, "10": 22, "14": 18 },
      "productive_hours": [9, 10, 14],
      "habit_consistency_score": 78,
      "behavior_summary": "Most productive in late morning..."
    }
  }
}
```

### Behavior Timeline
`GET /analytics/behavior/?days=7`

---

## Memory Insights

### List Insights
`GET /memory/insights/`  
`GET /memory/insights/?type=personality`

Types: `personality`, `behavior`, `preference`, `goal`, `skill`, `challenge`, `relationship`

**Response:**
```json
{
  "status": "success",
  "results": [
    {
      "id": "uuid",
      "insight_type": "behavior",
      "content": "Most productive between 9-11am",
      "confidence": 0.87,
      "evidence_count": 5,
      "is_active": true
    }
  ]
}
```

---

## Recommendations

### List Recommendations
`GET /recommendations/`  
`GET /recommendations/?status=pending`

Statuses: `pending`, `accepted`, `dismissed`, `completed`

### Accept Recommendation
`PATCH /recommendations/{id}/accept/`

### Dismiss Recommendation
`PATCH /recommendations/{id}/dismiss/`

---

## Error Responses

All errors follow this format:

```json
{
  "status": "error",
  "code": 400,
  "message": "Human-readable error message",
  "errors": {
    "email": ["This field is required."]
  },
  "request_id": "uuid"
}
```

| Code | Meaning |
|------|---------|
| 400 | Bad request / validation error |
| 401 | Authentication required |
| 403 | Permission denied |
| 404 | Resource not found |
| 429 | Rate limit exceeded |
| 500 | Internal server error |

---

## Interactive Docs

- Swagger UI: `https://yourdomain.com/api/docs/`
- ReDoc: `https://yourdomain.com/api/redoc/`
- OpenAPI schema: `https://yourdomain.com/api/schema/`
