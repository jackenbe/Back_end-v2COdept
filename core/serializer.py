from rest_framework import serializers
from .models import Script, Skill
from django.contrib.auth.models import User

class ScriptFileViewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Script
        fields = ['id', 'author', 'name', 'created_at', 'updated_at']

class ScriptOpenSerializer(serializers.ModelSerializer):
    class Meta:
        model = Script
        fields = ['id', 'author', 'name', 'created_at', 'updated_at', 'code', 'language']

class ScriptCreateSerializer(serializers.ModelSerializer):
    name = serializers.CharField(max_length=30)
    code = serializers.CharField(style={'base_template': 'textarea.html'}, trim_whitespace=False)
    language = serializers.CharField(max_length=30, allow_blank=False)

    class Meta:
        model = Script
        fields = ['name','code', 'language']

    def create(self, validated_data):
        user = self.context['request'].user
        return Script.objects.create(author=user, **validated_data)

class ScriptUpdateSerializer(serializers.ModelSerializer):
    name = serializers.CharField(max_length=30)
    code = serializers.CharField(style={'base_template': 'textarea.html'}, trim_whitespace=False)
    language = serializers.CharField(max_length=30, allow_blank=False)

    class Meta:
        model = Script
        fields = ['name','code', 'language']

    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        instance.code = validated_data.get('code', instance.code)
        instance.language = validated_data.get('language', instance.language)
        instance.save()
        return instance

class ScriptFileSendSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField()
    class Meta:
        model = Script
        fields=['id']


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields=['username', 'password']

    def create(self, validated_data):
        user = User(
            username = validated_data['username']
        )
        user.set_password(validated_data['password'])
        user.save()
        return user