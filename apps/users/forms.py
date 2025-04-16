from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User

class UserRegisterForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('email', 'full_name')

class UserLoginForm(forms.Form):
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)
