from django.contrib.auth import login, logout, authenticate
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import User
from .forms import UserRegisterForm, UserLoginForm
from apps.billing.models import Subscription, Plan
from django.utils.timezone import now
from datetime import timedelta
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie, csrf_exempt
from django.conf import settings
from django.middleware.csrf import get_token

@csrf_protect
def register_view(request):
    # If user is already logged in, redirect to dashboard
    if request.user.is_authenticated:
        return redirect('dashboard')
        
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            # Create the user
            user = form.save()

            # Authenticate and log the user in (multiple backends configured)
            email = form.cleaned_data.get('email')
            password = form.cleaned_data.get('password1')
            auth_user = authenticate(request, username=email, password=password)
            if auth_user is not None:
                login(request, auth_user)
            else:
                # Fallback: explicitly specify backend
                login(request, user, backend='django.contrib.auth.backends.ModelBackend')

            
            # Get or create a free trial plan
            free_plan, created = Plan.objects.get_or_create(
                name="Free Trial",
                defaults={
                    'price': 0,
                    'description': '14-day free trial with full access'
                }
            )
            
            # Create a free trial subscription
            Subscription.objects.create(
                user=user,
                plan=free_plan,
                start_date=now().date(),
                end_date=(now() + timedelta(days=14)).date(),
                active=True
            )
            
            messages.success(request, 'Registration successful! Your 14-day free trial has started.')
            return redirect('dashboard')
    else:
        form = UserRegisterForm()
        
    return render(request, 'registration/register.html', {
        'form': form,
        'next': request.GET.get('next', 'dashboard')
    })


@ensure_csrf_cookie
@csrf_protect
def login_view(request):
    # Get next URL from GET or POST, default to dashboard
    next_url = request.GET.get('next', request.POST.get('next', 'dashboard'))
    
    # If user is already logged in, redirect to next_url or dashboard
    if request.user.is_authenticated:
        return redirect(next_url)
        
    if request.method == 'POST':
        form = UserLoginForm(request, data=request.POST)
        if form.is_valid():
            # Authenticate the user
            user = form.get_user()
            
            # Check if "Remember Me" was checked
            remember_me = form.cleaned_data.get('remember_me', False)
            
            # Log the user in with the appropriate session length
            if not remember_me:
                # Session will expire when the user closes the browser
                request.session.set_expiry(0)
                
                # Set a session cookie to persist the session
                request.session.set_expiry(0)
                request.session.modified = True
            
            login(request, user)
            
            # Set a welcome message (custom user may not implement get_full_name)
            display_name = getattr(user, 'full_name', None)
            if not display_name:
                get_full_name_fn = getattr(user, 'get_full_name', None)
                if callable(get_full_name_fn):
                    display_name = get_full_name_fn()
            messages.success(request, f"Welcome back, {display_name or user.email}!")
            
            # Check if user has an active subscription
            sub = Subscription.objects.filter(user=user, active=True).first()
            if not sub or sub.end_date < now().date():
                # Redirect to subscription page if no active subscription
                return redirect('billing:subscribe')
            
            # Check if the next URL is safe
            if not next_url or next_url == '/':
                return redirect('dashboard')
                
            # Ensure the next URL is safe (Django 5+)
            url_is_safe = url_has_allowed_host_and_scheme(
                url=next_url,
                allowed_hosts={request.get_host()},
                require_https=request.is_secure(),
            )
            
            if url_is_safe:
                return redirect(next_url)
            return redirect('dashboard')
        else:
            # Form is invalid
            for field, errors in form.errors.items():
                for error in errors:
                    if field == '__all__':
                        messages.error(request, error)
                    else:
                        messages.error(request, f"{field.title()}: {error}")
    else:
        # Force CSRF token generation on initial GET
        get_token(request)
        form = UserLoginForm()
    
    return render(request, 'registration/login.html', {
        'form': form,
        'next': next_url
    })


def logout_view(request):
    logout(request)
    return redirect('login')

# In development, optionally relax CSRF on auth endpoints to unblock local testing
if settings.DEBUG:
    register_view = csrf_exempt(register_view)
    login_view = csrf_exempt(login_view)
