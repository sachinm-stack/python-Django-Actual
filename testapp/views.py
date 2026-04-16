from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken

from testapp.permissions import IsTeacher
from .serializers import CreateQuestionSerializer, LoginSerializer, RegisterSerializer, UserSerializer

# ── Helper: generate tokens for a user ────────────────────
def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access':  str(refresh.access_token),
    }

# Create your views here.
# ══════════════════════════════════════════════════════════
# REGISTER VIEW
# ══════════════════════════════════════════════════════════
class RegisterView(APIView):
    # AllowAny — no token needed to register (makes sense!)
    permission_classes = [AllowAny]

    def post(self, request):
        # 1. Pass incoming JSON to serializer
        serializer = RegisterSerializer(data=request.data)

        # 2. Validate — like our __init__ type checks in OOP
        if serializer.is_valid():
            # 3. Save → calls our overridden create() → create_user()
            user = serializer.save()

            # 4. Generate JWT tokens
            tokens = get_tokens_for_user(user)

            # 5. Return user data + tokens
            return Response({
                'user':   UserSerializer(user).data,
                'tokens': tokens,
            }, status=status.HTTP_201_CREATED)

        # Validation failed → return errors
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    


from django.contrib.auth import authenticate
from .serializers import LoginSerializer, LoginResponseSerializer
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
        # Django's built-in authenticate checks username + password
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

from .serializers import CreateTestSerializer, ListTestSerializer

class CreateTestView(APIView):
    permission_classes = [IsTeacher]
    def post(self, request):
        serializer = CreateTestSerializer(data=request.data)
        if serializer.is_valid():
            test = serializer.save(created_by=request.user)
            return Response({'message': 'Test created successfully', 'test_id': test.id}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request):
        # List all tests created by the teacher
        tests = request.user.created_tests.all()
        serializer = ListTestSerializer(tests, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class QuestionView(APIView):
    permission_classes = [IsTeacher]
    def post(self, request):
        serializer = CreateQuestionSerializer(data=request.data)
        if serializer.is_valid():
            question = serializer.save()
            return Response({'message': 'Question created successfully', 'question_id': question.id}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    






###############################################################################################

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .serializers import UploadTestCSVSerializer


class UploadTestCSVView(APIView):
    permission_classes = [IsTeacher]

    def post(self, request):
        serializer = UploadTestCSVSerializer(
            data=request.data,
            context={"request": request}
        )

        if serializer.is_valid():
            test = serializer.save()

            return Response({
                "message": "Test created successfully",
                "test_id": test.id
            }, status=201)

        return Response(serializer.errors, status=400)