from django.shortcuts import render
from rest_framework.views import APIView
from users.serializers import LoginSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.response import Response

# Create your views here.
class LoginView(APIView):
    def post(self, request):
        serializer = LoginSerializer(data=request.data)

        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data["user"]

        refresh = RefreshToken.for_user(user)

        return Response({
            "access" : str(refresh.access_token),
            "refresh" : str(refresh)
        })