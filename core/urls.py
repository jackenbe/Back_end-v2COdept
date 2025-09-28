from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import list_scripts, RegisterView, open_script, create_script, update_script, ai_advice, get_chat_history

app_name = "core"
urlpatterns = [
    path('api/token', TokenObtainPairView.as_view(), name='taken_obtain_pair'),
    path('api/register/', RegisterView.as_view(), name='register'),
    path('api/token/refresh', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/scripts/', list_scripts, name='list_script'),
    path('api/get-script/', open_script, name='open_script'),
    path('api/create-script/', create_script, name='create_script'),
    path('api/update/<int:pk>/', update_script, name='update_script'),
    path('api/ai-advice/', ai_advice, name='ai_advice'),
    path('api/chat-history/', get_chat_history, name='get_chat_history'),

]