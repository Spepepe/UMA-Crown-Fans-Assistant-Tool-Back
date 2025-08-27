from rest_framework import serializers
from .models import *


class UmamusumeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Umamusume
        fields = '__all__'


class UmamusumeActerSerializer(serializers.ModelSerializer):
    umamusume = UmamusumeSerializer(read_only=True)
    
    class Meta:
        model = UmamusumeActer
        fields = '__all__'


class LiveSerializer(serializers.ModelSerializer):
    class Meta:
        model = Live
        fields = '__all__'


class VocalUmamusumeSerializer(serializers.ModelSerializer):
    umamusume = UmamusumeSerializer(read_only=True)
    
    class Meta:
        model = VocalUmamusume
        fields = '__all__'


class RaceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Race
        fields = '__all__'


class RegistUmamusumeSerializer(serializers.ModelSerializer):
    umamusume = UmamusumeSerializer(read_only=True)
    
    class Meta:
        model = RegistUmamusume
        fields = '__all__'


class JewelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Jewel
        fields = '__all__'


class UserPersonalSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserPersonal
        fields = ['user_name', 'email']


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=7)
    
    class Meta:
        model = UserPersonal
        fields = ['user_name', 'password', 'email']
    
    def create(self, validated_data):
        password = validated_data.pop('password')
        user = UserPersonal(**validated_data)
        user.set_password(password)
        user.save()
        return user