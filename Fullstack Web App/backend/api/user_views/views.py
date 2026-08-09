from rest_framework.viewsets import ModelViewSet
from users.serializers import UserSerializer
from users.models import User

# Create your views here.
class UserViewSet(ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer