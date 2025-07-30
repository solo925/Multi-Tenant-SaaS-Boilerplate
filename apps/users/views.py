from django.contrib.auth import login, logout, authenticate
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import User
from .forms import UserRegisterForm, UserLoginForm

def register_view(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, 'Registration successful! You can now log in.')
            return redirect('login')
    else:
        form = UserRegisterForm()
    return render(request, 'registration/register.html', {'form': form})


def login_view(request):
    next_url = request.GET.get('next') or request.POST.get('next')
    if request.user.is_authenticated:
        print("Already authenticated, redirecting...")
        return redirect(next_url or 'dashboard')
    if request.method == 'POST':
        form = UserLoginForm(request.POST)
        print("POST data:", request.POST)
        if form.is_valid():
            print("Form is valid")
            email = form.cleaned_data.get('email')
            password = form.cleaned_data.get('password')
            # Fix: use username=email for custom user model
            user = authenticate(request, username=email, password=password)
            print("Authenticated user:", user)
            if user:
                login(request, user)
                print("Login successful, redirecting...")
                return redirect(next_url or 'dashboard')
            messages.error(request, 'Invalid login credentials')
        else:
            print("Form is not valid:", form.errors)
    else:
        form = UserLoginForm()
    return render(request, 'registration/login.html', {'form': form, 'next': next_url})


def logout_view(request):
    logout(request)
    return redirect('login')
