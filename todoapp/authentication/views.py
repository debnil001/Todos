import threading
from django.contrib import messages
from django.shortcuts import redirect, render
from django.urls import reverse
from validate_email import validate_email
from .models import User
from django.contrib.auth import authenticate,login,logout
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_decode,urlsafe_base64_encode
from django.utils.encoding import force_bytes,force_str
from .utils import generate_token
from django.core.mail import EmailMessage
from django.conf import settings


class EmailThread(threading.Thread):
    def __init__(self,email):
        self.email = email
        threading.Thread.__init__(self)

    def run(self):
        self.email.send()


def send_activation_email(user,request):
    current_site=get_current_site(request)
    email_subject="Activate your account"
    email_body=render_to_string("authentication/activate.html",{
        'user':user,
        'domain':current_site,
        'uid':urlsafe_base64_encode(force_bytes(user.pk)),
        'token':generate_token.make_token(user)
    })

    email=EmailMessage(subject=email_subject,body=email_body,from_email=settings.EMAIL_FROM_USER,
                 to=[user.email])
    EmailThread(email).start()

def register(request):
    context=dict()
    if request.method == 'POST':
        context={'has_error': False,'data': request.POST}
        email=request.POST.get('email')
        username=request.POST.get('username')
        password=request.POST.get('password')
        password2=request.POST.get('password2')

        if len(password)<6:
            messages.add_message(request,messages.ERROR,"Password must be at least 6 characters")
            context['has_error']=True

        if password2!=password:
            messages.add_message(request,messages.ERROR,"Password mismatch")
            context['has_error']=True

        if not validate_email(email):
            messages.add_message(request,messages.ERROR,"Enter a valid a email address")
            context['has_error']=True

        if not username:
            messages.add_message(request,messages.ERROR,"Username is required")
            context['has_error']=True

        if User.objects.filter(username=username).exists():
            messages.add_message(request,messages.ERROR,"Username already exist,choose another")
            context['has_error']=True

        if User.objects.filter(email=email).exists():
            messages.add_message(request,messages.ERROR,"Email id already taken, choose another")
            context['has_error']=True

        if context['has_error']:
            return render(request,'authentication/register.html',context)
        
        user=User.objects.create_user(username=username,email=email)
        user.set_password(password)
        user.save()

        send_activation_email(user,request)
        messages.add_message(request,messages.SUCCESS,"Verification link has been sent to registered " 
                             "email address")
        return redirect('login')
    return render(request,'authentication/register.html')


def login_user(request):
    if request.method == 'POST':
        context={'data':request.POST}
        username=request.POST.get('username')
        password=request.POST.get('password')

        user=authenticate(request,username=username,password=password)
        if not user.is_email_verified:
            messages.add_message(request,messages.ERROR,"Email is not verified please check your mail box")
            return render(request,'authentication/login.html',context)

        if not user:
            messages.add_message(request,messages.ERROR,"Invalid credentials")
            return render(request,'authentication/login.html',context)
        login(request,user)
        messages.add_message(request,messages.SUCCESS,f"Welcome {user.username}")

        return redirect(reverse('index'))
    return render(request,'authentication/login.html')

def logout_user(request):

    logout(request)
    messages.add_message(request,messages.SUCCESS,"You have Successfully Logout")

    return redirect(reverse('login'))

def activate_user(request,uidb64,token):

    try:
        uid=force_str(urlsafe_base64_decode(uidb64))
        user=User.objects.get(pk=uid)
    except Exception as e:
        user=None
    if user and generate_token.check_token(user,token):
        user.is_email_verified=True
        user.save()

        messages.add_message(request,messages.SUCCESS,"Email is verified, you can now login")

        return redirect(reverse('index'))
    
    return render(request,'authentication/activation-failed.html',{'user':user})