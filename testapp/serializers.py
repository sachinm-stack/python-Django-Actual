from rest_framework import serializers
from .models import Test, User, Question, Option   # ✅ ADDED Question, Option

# ── 2. Register serializer (for creating a new user) ──────
class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)
    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)
    role = serializers.ChoiceField(choices=User.ROLE_CHOICES, required=True)
    email = serializers.EmailField(required=True)

    class Meta:
        model  = User
        fields = ['username', 'email', 'password', 'role', 'first_name', 'last_name']

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


# ── 1. User serializer (read-only, for showing user info) ──
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model  = User
        fields = ['id', 'username', 'email', 'role', 'first_name', 'last_name']


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)


class LoginResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'role']


class CreateTestSerializer(serializers.ModelSerializer):
    class Meta:
        model = Test
        fields = ['title', 'time_limit']


class ListTestSerializer(serializers.ModelSerializer):
    created_by = serializers.CharField(source='created_by.username')

    class Meta:
        model = Test
        fields = ['id', 'title', 'created_by', 'time_limit', 'is_published', 'created_at']


# ─────────────────────────────────────────────────────────
# ✅ ADD BELOW (NEW FOR QUESTION + OPTION)
# ─────────────────────────────────────────────────────────

class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = ['id', 'test', 'text', 'question_type', 'marks']


class OptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Option
        fields = ['id', 'question', 'text', 'is_correct']


# 🔥 (Optional but IMPORTANT for next step)
class QuestionWithOptionsSerializer(serializers.ModelSerializer):
    options = OptionSerializer(many=True, read_only=True)

    class Meta:
        model = Question
        fields = ['id', 'text', 'question_type', 'marks', 'options']