from djoser.serializers import UserCreateSerializer as DjoserUserCreateSerializer
from djoser.serializers import UserSerializer as DjoserUserSerializer


class UserCreateSeriaizer(DjoserUserCreateSerializer):
    class Meta(DjoserUserCreateSerializer.Meta):
        fields = ['id', 'username', 'password',
                  'email', 'first_name', 'last_name']


class Userserializer(DjoserUserSerializer):
    class Meta(DjoserUserSerializer.Meta):
        fields = ['id', 'username', 'email', 'first_name', 'last_name']
