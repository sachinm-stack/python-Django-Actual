from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import RegisterSerializer, UserSerializer

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