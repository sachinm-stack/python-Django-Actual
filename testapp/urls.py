
from django.contrib import admin
from django.urls import include, path
from .views import CreateTestView, LoginView, RegisterView, CreateQuestionView  # ✅ added

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),

    path('create-test/', CreateTestView.as_view(), name='create-test'),
    path('list-tests/', CreateTestView.as_view(), name='list-tests'),

    path('create-question/', CreateQuestionView.as_view(), name='create-question'),  # ✅ NEW
]