from .models import Script, Skill, ChatMessage
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import generics
from .serializer import (
    ScriptFileViewSerializer,
    RegisterSerializer,
    ScriptFileSendSerializer,
    ScriptOpenSerializer,
    ScriptCreateSerializer,
    ScriptUpdateSerializer,

)
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
import os
from langchain_core.prompts import PromptTemplate
from pydantic import BaseModel, Field, ValidationError
from langchain_core.output_parsers import PydanticOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI
from django.conf import settings
from langchain_core.exceptions import OutputParserException

class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def list_scripts(request):
    scripts = Script.objects.filter(author=request.user)
    serialize = ScriptFileViewSerializer(scripts, many=True)
    return Response(serialize.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def open_script(request):
    serialize = ScriptFileSendSerializer(data=request.data)
    if serialize.is_valid():
        id = serialize.validated_data.get('id')
        item = get_object_or_404(Script, id=id, author=request.user)
        output_serializer = ScriptOpenSerializer(item)
        return Response(output_serializer.data, status=status.HTTP_200_OK)
    return Response(serialize.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_script(request):
    serializer = ScriptCreateSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        serializer.save()

        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_script(request, pk):
    script = get_object_or_404(Script, pk =pk, author=request.user)

    serializer = ScriptUpdateSerializer(script, data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_202_ACCEPTED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# -------------------------------------
# AI AGENT PART
# -------------------------------------

class TutorResponse(BaseModel):
    explanation: str = Field(description="A detailed explanation of the code, including what it does and how it could be improved.")
    hints: list[str] = Field(description="A list of hints to guide the user toward a solution.")
    improvements: list[str] = Field(description="A list of specific improvements for the code's efficiency, readability, or best practices.")
    skill_level: int = Field(description="The student's current coding skill level as an integer from 1 to 100. Assess this based on all the provided code and conversation history.")
    lesson_plan: str = Field(description="A lesson plan or a response to the student's request for one. Generate a plan only if the student asks for one.")


# Create the agent chain as a reusable component
def create_tutor_agent():
    os.environ['GOOGLE_API_KEY'] = settings.GEMINI_API_KEY
    print(f"DEBUG: GOOGLE_API_KEY is set: {bool(os.environ.get('GOOGLE_API_KEY'))}")
    model = ChatGoogleGenerativeAI(model="gemini-2.0-flash")
    parser = PydanticOutputParser(pydantic_object=TutorResponse)

    prompt_template = """
    You are a professional AI coding tutor. Your priority is providing **clear, actionable, and concise advice** to the student.
    Break down complex explanations into simple steps and use bullet points for lists (hints and improvements).
    Your tone must be encouraging and knowledgeable, but **never verbose**. Explain the 'why' briefly, then focus on the 'how'.
    You will analyze the student's code, their questions, and all past conversation history.
    You will also track their coding skill level (1-100) based on all their provided code.
    You will provide a lesson plan if and only if they ask for one.
    The user is a visual learner so don't chase them away being wordy.

    Your response must strictly follow this JSON format:
    {format_instructions}

    Student's Code Language: {language}

    Student's Code:
    ```
    {code}
    ```

    All-Time Code and Chat History:
    {all_time_history}

    Student's Current Question: {user_message}
    """

    prompt = PromptTemplate(
        template=prompt_template,
        input_variables=["user_message", "code", "language", "all_time_history"],
        partial_variables={"format_instructions": parser.get_format_instructions()},
    )
    return prompt | model | parser


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def ai_advice(request):
    try:
        user_message = request.data.get('user_message')
        user_code = request.data.get('code')
        user_language = request.data.get('language')
        script_id = request.data.get('script_id')  # Get the script ID from the request

        if not all([user_message, script_id]):
            return Response({'error': 'Message and script_id are required.'}, status=status.HTTP_400_BAD_REQUEST)

        # Retrieve the specific script object
        script = get_object_or_404(Script, id=script_id, author=request.user)

        # Save the user's message to the database
        ChatMessage.objects.create(
            user=request.user,
            script=script,
            role='user',
            content=user_message
        )

        # Retrieve ALL chat history and code for the user, regardless of script
        all_user_messages = ChatMessage.objects.filter(user=request.user).order_by('timestamp')
        all_user_scripts = Script.objects.filter(author=request.user).order_by('id')

        # Format the all-time history for the prompt
        all_time_history = ""
        for msg in all_user_messages:
            all_time_history += f"{msg.role.capitalize()}: {msg.content}\n"

        for s in all_user_scripts:
            all_time_history += f"Script: {s.name} ({s.language})\nCode:\n```\n{s.code}\n```\n"

        # Create the agent and get the AI's response
        agent = create_tutor_agent()
        agent_response = agent.invoke(
            {
                "user_message": user_message,
                "code": user_code,
                "language": user_language,
                "all_time_history": all_time_history
            }
        )

        # The response is a Pydantic object, convert it to a dictionary
        response_data = agent_response.dict()

        # --- FIX: Format lists into proper Markdown bullet points for readability ---
        hint_list = "\n".join([f"* {h}" for h in response_data['hints']])
        improvement_list = "\n".join([f"* {i}" for i in response_data['improvements']])

        # Reconstruct the response text with clean Markdown formatting
        ai_response_text = f"""### Explanation
{response_data['explanation']}

### Actionable Steps (Hints)
{hint_list}

### Core Improvements
{improvement_list}

### Skill Level
{response_data['skill_level']}/100

### Lesson Plan
{response_data['lesson_plan'] or 'No lesson plan requested.'}"""

        # Save the AI's response to the database
        ChatMessage.objects.create(
            user=request.user,
            script=script,
            role='ai',
            content=ai_response_text
        )

        # Update or create the user's skill level
        skill_level, created = Skill.objects.get_or_create(
            user=request.user,
            name=user_language,
            defaults={'level': response_data['skill_level']}
        )
        if not created:
            skill_level.level = response_data['skill_level']
            skill_level.save()

        return Response({'response': ai_response_text})

    except (OutputParserException, ValidationError) as e:
        # Log the raw AI response if the parser fails
        return Response({'error': 'AI provided an unreadable response. Please try again.'},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET']) # FIX: Changed from ['POST'] to ['GET']
@permission_classes([IsAuthenticated])
def get_chat_history(request):
    """
    Fetches the chat message history for a specific script.
    """
    try:
        # FIX: Retrieve script_id from query parameters (URL) instead of request.data
        script_id = request.query_params.get('script_id')

        if not script_id:
            return Response({'error': 'script_id is required.'}, status=status.HTTP_400_BAD_REQUEST)

        # Ensure the script exists and belongs to the user
        script = get_object_or_404(Script, id=script_id, author=request.user)

        # Fetch messages for that specific script, ordered by timestamp
        messages = ChatMessage.objects.filter(script=script).order_by('timestamp')

        history_data = [
            {
                'role': msg.role,
                'content': msg.content,
                'timestamp': msg.timestamp.isoformat()
            }
            for msg in messages
        ]

        return Response({'history': history_data})

    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
