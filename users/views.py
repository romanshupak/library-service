from drf_spectacular.utils import extend_schema
from rest_framework import generics
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.permissions import IsAuthenticated
from rest_framework.settings import api_settings
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.authtoken.serializers import AuthTokenSerializer

from users.serializers import UserSerializer


@extend_schema(
        summary="Create a new user",
        description="This endpoint allows you to create a new user "
                    "by providing the necessary email and password.",
        request=UserSerializer,
        responses={
            201: UserSerializer,
            400: "Bad Request",
        },
)
class CreateUserView(generics.CreateAPIView):
    serializer_class = UserSerializer


@extend_schema(
    summary="Retrieve user profile",
    description="This endpoint allows you to retrieve the profile "
                "of the authenticated user.",
    request=UserSerializer,
    responses={
        200: UserSerializer,
        400: "Bad Request",
        403: "Forbidden",
    }
)
class ManageUserView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    authentication_classes = (JWTAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get_object(self):
        return self.request.user.objects.prefetch_related("groups", "user_permissions")


@extend_schema(
    summary="User login",
    description="This endpoint allows users to log in by providing "
                "their email and password, and it returns an authentication token.",
    request=AuthTokenSerializer,
    responses={
        200: "Token",
        400: "Bad Request",
    },
)
class LoginUserView(ObtainAuthToken):
    renderer_classes = api_settings.DEFAULT_RENDERER_CLASSES
    serializer_class = AuthTokenSerializer
