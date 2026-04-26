from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView


class ContractorTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["contractor_id"] = user.pk
        token["email"] = user.email
        token["is_pro"] = user.is_pro()
        return token


class ContractorTokenObtainPairView(TokenObtainPairView):
    serializer_class = ContractorTokenObtainPairSerializer
