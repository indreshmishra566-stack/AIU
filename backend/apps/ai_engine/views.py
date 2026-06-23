"""
AIU — AI Engine: API Views
Chat, streaming chat, conversation management endpoints.
"""

import json
import logging

from django.http import StreamingHttpResponse
from drf_spectacular.utils import extend_schema
from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework.viewsets import ViewSet

from apps.memory.models import Conversation, Message
from apps.memory.serializers import ConversationSerializer, MessageSerializer
from .orchestrator import AIRequest, orchestrator

logger = logging.getLogger("ai_engine")


# ─────────────────────────────────────────────────────────────────────────────
# Serializers
# ─────────────────────────────────────────────────────────────────────────────

class ChatRequestSerializer(serializers.Serializer):
    message = serializers.CharField(max_length=4000)
    conversation_id = serializers.UUIDField(required=False, allow_null=True)
    coach_mode = serializers.ChoiceField(
        choices=["friendly", "mentor", "strict", "analytical"],
        default="friendly",
    )
    stream = serializers.BooleanField(default=False)
    context = serializers.DictField(required=False, default=dict)


class ChatResponseSerializer(serializers.Serializer):
    content = serializers.CharField()
    conversation_id = serializers.UUIDField()
    message_id = serializers.UUIDField()
    tokens_used = serializers.IntegerField()
    model = serializers.CharField()
    retrieved_memories = serializers.IntegerField()
    latency_ms = serializers.FloatField()


class AIChatThrottle(ScopedRateThrottle):
    scope = "ai_queries"


# ─────────────────────────────────────────────────────────────────────────────
# Chat View
# ─────────────────────────────────────────────────────────────────────────────

class ChatView(APIView):
    """
    POST /api/v1/ai/chat/
    Supports both normal and streaming responses.
    """

    throttle_classes = [AIChatThrottle]

    @extend_schema(
        request=ChatRequestSerializer,
        responses={200: ChatResponseSerializer},
        summary="Send a message to your AI",
    )
    def post(self, request):
        serializer = ChatRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        # 🔥 STREAM MODE
        if data.get("stream"):
            return self._stream_response(request, data)

        # 🔥 NORMAL MODE
        ai_req = AIRequest(
            user_id=str(request.user.id),
            message=data["message"],
            conversation_id=str(data["conversation_id"]) if data.get("conversation_id") else None,
            coach_mode=data["coach_mode"],
            extra_context=data.get("context", {}),
        )

        ai_resp = orchestrator.process(ai_req)

        request.user.update_last_activity()

        return Response(
            {
                "status": "success",
                "data": {
                    "content": ai_resp.content,
                    "conversation_id": ai_resp.conversation_id,
                    "message_id": ai_resp.message_id,
                    "tokens_used": ai_resp.tokens_used,
                    "model": ai_resp.model,
                    "retrieved_memories": ai_resp.retrieved_memories,
                    "latency_ms": ai_resp.latency_ms,
                },
            }
        )

    # ─────────────────────────────────────────────────────────────────────────
    # Streaming (FIXED)
    # ─────────────────────────────────────────────────────────────────────────

    def _stream_response(self, request, data: dict):
        """Return Server-Sent Events stream."""

        ai_req = AIRequest(
            user_id=str(request.user.id),
            message=data["message"],
            conversation_id=str(data["conversation_id"]) if data.get("conversation_id") else None,
            coach_mode=data["coach_mode"],
            stream=True,
            extra_context=data.get("context", {}),
        )

        def event_stream():
            try:
                for chunk in orchestrator.stream(ai_req):

                    # ✅ FIX: always send valid SSE format
                    if isinstance(chunk, dict):
                        yield f"data: {json.dumps(chunk)}\n\n"
                    else:
                        yield f"data: {str(chunk)}\n\n"

                yield "data: [DONE]\n\n"

            except Exception as exc:
                logger.exception("Stream error", extra={"user_id": str(request.user.id)})
                yield f"data: [ERROR] {str(exc)}\n\n"

        response = StreamingHttpResponse(
            event_stream(),
            content_type="text/event-stream",
        )
        response["Cache-Control"] = "no-cache"
        response["X-Accel-Buffering"] = "no"
        return response


# ─────────────────────────────────────────────────────────────────────────────
# Conversation APIs
# ─────────────────────────────────────────────────────────────────────────────

class ConversationViewSet(ViewSet):

    def list(self, request):
        conversations = (
            Conversation.objects.filter(user=request.user, is_archived=False)
            .only("id", "title", "summary", "last_message_at", "topics", "coach_mode")
            .order_by("-last_message_at")[:50]
        )
        serializer = ConversationSerializer(conversations, many=True)
        return Response({"status": "success", "results": serializer.data})

    def retrieve(self, request, pk=None):
        try:
            conversation = Conversation.objects.get(id=pk, user=request.user)
        except Conversation.DoesNotExist:
            return Response({"status": "error", "message": "Not found"}, status=404)

        messages = (
            Message.objects.filter(conversation=conversation)
            .order_by("created_at")
            .only("id", "role", "content", "created_at", "model_used")
        )

        return Response(
            {
                "status": "success",
                "conversation": ConversationSerializer(conversation).data,
                "messages": MessageSerializer(messages, many=True).data,
            }
        )

    def destroy(self, request, pk=None):
        updated = Conversation.objects.filter(id=pk, user=request.user).update(is_archived=True)
        if not updated:
            return Response({"status": "error", "message": "Not found"}, status=404)
        return Response(status=status.HTTP_204_NO_CONTENT)