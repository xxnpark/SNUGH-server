from django.contrib.auth.models import User
from rest_framework import serializers


class UserSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField()
    email = serializers.CharField()
    year = serializers.SerializerMethodField()
    full_name = serializers.SerializerMethodField()
    major = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "year",
            "full_name",
            "status",
            "major"
        )

    def get_year(self, user):
        userprofile = user.userprofile
        return userprofile.year

    def get_status(self, user):
        userprofile = user.userprofile
        return userprofile.status

    def get_major(self, user):
        ls = []
        usermajors = user.usermajor.all()
        for usermajor in usermajors:
            body = {"id": usermajor.major.id, "name": usermajor.major.major_name, "type": usermajor.major.major_type}
            ls.append(body)
        return ls

    def get_full_name(self, user):
        return user.first_name
