from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from apps.ai_agent.models import Conversation, ChatMessage
from apps.ai_agent.serializers import ConversationSerializer, ChatMessageSerializer
from apps.ai_agent.agent import ConversationalAgentOrchestrator


class ConversationListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile = request.user.profile
        convs = Conversation.objects.filter(profile=profile).order_by('-last_activity')
        serializer = ConversationSerializer(convs, many=True)
        return Response(serializer.data)

    def post(self, request):
        profile = request.user.profile
        title = request.data.get('title', 'Opportunity Discovery Session')
        conv = Conversation.objects.create(profile=profile, title=title)
        return Response(ConversationSerializer(conv).data, status=status.HTTP_201_CREATED)


class ChatMessageView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, id):
        profile = request.user.profile
        try:
            conv = Conversation.objects.get(id=id, profile=profile)
        except Conversation.DoesNotExist:
            return Response({"error": "Conversation not found."}, status=status.HTTP_404_NOT_FOUND)

        messages = conv.messages.all().order_by('created_at')
        serializer = ChatMessageSerializer(messages, many=True)
        return Response({
            "conversation_id": str(conv.id),
            "title": conv.title,
            "messages": serializer.data
        })

    def post(self, request, id):
        profile = request.user.profile
        user_message = request.data.get('message', '').strip()
        if not user_message:
            return Response({"error": "Message content cannot be empty."}, status=status.HTTP_400_BAD_REQUEST)

        result = ConversationalAgentOrchestrator.process_message(
            profile=profile,
            user_message=user_message,
            conversation_id=str(id)
        )
        return Response(result)
