from rest_framework import generics
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.permissions import IsAuthenticated
from rest_framework.settings import api_settings
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.authtoken.serializers import AuthTokenSerializer

from users.serializers import UserSerializer


class CreateUserView(generics.CreateAPIView):
    serializer_class = UserSerializer


class ManageUserView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    authentication_classes = (JWTAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get_object(self):
        return self.request.user.objects.prefetch_related("groups", "user_permissions")


class LoginUserView(ObtainAuthToken):
    renderer_classes = api_settings.DEFAULT_RENDERER_CLASSES
    serializer_class = AuthTokenSerializer
