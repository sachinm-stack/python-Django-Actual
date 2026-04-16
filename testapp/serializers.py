from rest_framework import serializers
from .models import Question, Test, User

# ── 2. Register serializer (for creating a new user) ──────
class RegisterSerializer(serializers.ModelSerializer):
    # write_only=True → password goes IN but never comes back out
    password = serializers.CharField(write_only=True, min_length=6)
    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)
    role = serializers.ChoiceField(choices=User.ROLE_CHOICES,required=True)
    email = serializers.EmailField(required=True)

    class Meta:
        model  = User
        fields = ['username', 'email', 'password', 'role', 'first_name', 'last_name']

    def create(self, validated_data):
        # Override create() — like method overriding in OOP
        # We MUST use create_user() so password gets hashed
        return User.objects.create_user(**validated_data)


# ── 1. User serializer (read-only, for showing user info) ──
class UserSerializer(serializers.ModelSerializer):
    # ModelSerializer = inheritance from DRF base class
    # Meta inner class = tells it WHICH model and WHICH fields
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


class CreateQuestionSerializer(serializers.ModelSerializer):
    marks = serializers.IntegerField(required=True, min_value=1)
    class Meta:
        model = Question
        fields = ['test', 'text', 'question_type', 'marks']


################################################################################
from rest_framework import serializers


class CSVQuestionSerializer(serializers.Serializer):
    question = serializers.CharField()
    question_type = serializers.ChoiceField(choices=['mcq', 'text'])
    marks = serializers.IntegerField(required=False, default=1)

    option1 = serializers.CharField(required=False, allow_blank=True)
    option2 = serializers.CharField(required=False, allow_blank=True)
    option3 = serializers.CharField(required=False, allow_blank=True)
    option4 = serializers.CharField(required=False, allow_blank=True)

    correct_option = serializers.CharField(required=False, allow_blank=True)

    def validate(self, data):
        q_type = data.get('question_type')

        options = [
            data.get('option1'),
            data.get('option2'),
            data.get('option3'),
            data.get('option4'),
        ]
        options = [opt for opt in options if opt]

        correct = data.get('correct_option')

        if q_type == 'mcq':
            if len(options) < 2:
                raise serializers.ValidationError("MCQ must have at least 2 options")

            if not correct:
                raise serializers.ValidationError("correct_option required")

            valid = any([
                correct in options,
                correct.isdigit() and 1 <= int(correct) <= len(options)
            ])

            if not valid:
                raise serializers.ValidationError("correct_option mismatch")

        if q_type == 'text':
            if any(options):
                raise serializers.ValidationError("Text question should not have options")

        return data
    
import csv
from django.db import transaction
from rest_framework import serializers
from .models import Test, Question, Option


class UploadTestCSVSerializer(serializers.Serializer):
    title = serializers.CharField()
    time_limit = serializers.IntegerField(default=30)
    is_published = serializers.BooleanField(default=False)
    file = serializers.FileField()

    def validate(self, data):

        file = data['file']

        try:
            decoded = file.read().decode('utf-8').splitlines()
            reader = csv.DictReader(decoded)
        except Exception:
            raise serializers.ValidationError("Invalid CSV file")

        validated_rows = []
        errors = []

        for idx, row in enumerate(reader, start=1):
            row_serializer = CSVQuestionSerializer(data=row)

            if row_serializer.is_valid():
                validated_rows.append(row_serializer.validated_data)
            else:
                errors.append({
                    "row": idx,
                    "errors": row_serializer.errors
                })

        if errors:
            raise serializers.ValidationError({
                "message": "CSV validation failed",
                "errors": errors
            })

        # store parsed data for create()
        data['validated_rows'] = validated_rows
        return data

    def create(self, validated_data):
        user = self.context['request'].user
        rows = validated_data.pop('validated_rows')

        with transaction.atomic():

            test = Test.objects.create(
                title=validated_data['title'],
                created_by=user,
                time_limit=validated_data.get('time_limit', 30),
                is_published=validated_data.get('is_published', False)
            )

            for row in rows:
                question = Question.objects.create(
                    test=test,
                    text=row['question'],
                    question_type=row['question_type'],
                    marks=row.get('marks', 1)
                )

                if row['question_type'] == 'mcq':
                    options = [
                        row.get('option1'),
                        row.get('option2'),
                        row.get('option3'),
                        row.get('option4'),
                    ]
                    options = [opt for opt in options if opt]

                    correct = row.get('correct_option')

                    for idx, opt in enumerate(options):
                        Option.objects.create(
                            question=question,
                            text=opt,
                            is_correct=(
                                opt == correct or str(idx + 1) == correct
                            )
                        )

        return test
    