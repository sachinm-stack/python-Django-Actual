from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate

from testapp.permissions import IsTeacher
from .models import Question
from .serializers import (
    LoginSerializer, RegisterSerializer, UserSerializer,
    LoginResponseSerializer,
    CreateTestSerializer, ListTestSerializer,
    QuestionSerializer, OptionSerializer,
    QuestionWithOptionsSerializer
)

# ── Helper: generate tokens for a user ────────────────────
def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access':  str(refresh.access_token),
    }

# ══════════════════════════════════════════════════════════
# REGISTER VIEW
# ══════════════════════════════════════════════════════════
class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)

        if serializer.is_valid():
            user = serializer.save()
            tokens = get_tokens_for_user(user)

            return Response({
                'user':   UserSerializer(user).data,
                'tokens': tokens,
            }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ══════════════════════════════════════════════════════════
# LOGIN VIEW
# ══════════════════════════════════════════════════════════
class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        login_serializer = LoginSerializer(data=request.data)

        if not login_serializer.is_valid():
            return Response(login_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        username = login_serializer.validated_data['username']
        password = login_serializer.validated_data['password']

        user = authenticate(username=username, password=password)

        if user is not None:
            tokens = get_tokens_for_user(user)

            return Response({
                'user':   LoginResponseSerializer(user).data,
                'tokens': tokens,
            }, status=status.HTTP_200_OK)

        return Response(
            {'error': 'Invalid username or password'},
            status=status.HTTP_401_UNAUTHORIZED
        )


# ══════════════════════════════════════════════════════════
# CREATE + LIST TEST
# ══════════════════════════════════════════════════════════
class CreateTestView(APIView):
    permission_classes = [IsTeacher]

    def post(self, request):
        serializer = CreateTestSerializer(data=request.data)

        if serializer.is_valid():
            test = serializer.save(created_by=request.user)
            return Response({
                'message': 'Test created successfully',
                'test_id': test.id
            }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request):
        tests = request.user.created_tests.all()
        serializer = ListTestSerializer(tests, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


# ══════════════════════════════════════════════════════════
# CREATE QUESTION
# ══════════════════════════════════════════════════════════
class CreateQuestionView(APIView):
    permission_classes = [IsTeacher]

    def post(self, request):
        serializer = QuestionSerializer(data=request.data)

        if serializer.is_valid():
            test = serializer.validated_data['test']

            # 🔒 SECURITY: Only owner can add questions
            if test.created_by != request.user:
                return Response(
                    {"error": "You can only add questions to your own test"},
                    status=status.HTTP_403_FORBIDDEN
                )

            question = serializer.save()

            return Response({
                "message": "Question created successfully",
                "question_id": question.id
            }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ══════════════════════════════════════════════════════════
# CREATE OPTION
# ══════════════════════════════════════════════════════════
class CreateOptionView(APIView):
    permission_classes = [IsTeacher]

    def post(self, request):
        serializer = OptionSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response({
                "message": "Option created successfully"
            }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ══════════════════════════════════════════════════════════
# GET QUESTIONS WITH OPTIONS BY TEST
# ══════════════════════════════════════════════════════════
class ListQuestionsByTestView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, test_id):
        questions = Question.objects.filter(test_id=test_id)
        serializer = QuestionWithOptionsSerializer(questions, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)