from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend

class EmailOrUsernameBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        UserModel = get_user_model()
        try:
            # Try email first
            user = UserModel.objects.get(email=username)
        except UserModel.DoesNotExist:
            try:
                # Fallback to username
                user = UserModel.objects.get(username=username)
            except UserModel.DoesNotExist:
                return None
        if user.check_password(password):
            return user
        return None