
import re

from django.http import HttpResponse
from django.conf import settings
from django.core.mail import send_mail
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views.generic import View
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer, SignatureExpired
# from celery_tasks.tasks import send_register_active_email

from .models import User


# GET 127.0.0.1:8000/user/register
def register(request):
    """注册页面"""
    return render(request, 'register.html')


# POST 127.0.0.1:8000/user/register
def regiseter_handle(request):
    """注册业务逻辑"""
    # 接收数据
    username = request.POST.get('user_name')
    password = request.POST.get('pwd')
    email = request.POST.get('email')
    allow = request.POST.get('allow')

    # 验证数据
    if not all([username, password, email]):
        return render(request, 'register.html', {'err_msg': '数据不完整'})

    if not re.match(r'^[a-z0-9][\w.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
        return render(request, 'register.html', {'errmsg': '邮箱格式不正确'})

    if allow != 'on':
        return render(request, 'register.html', {'err_msg': '请同意协议'})

    try:
        user = User.objects.get(username=username)
    except Exception as e:
        user = None
    if user:
        return render(request, 'register.html', {'err_msg': '用户名已注册'})

    # 注册业务
    # user = User()
    # user.username = username
    # user.password = password
    # user.email = email
    # user.save()

    user = User.objects.create_user(username=username, password=password, email=email)
    # 是否激活修改为0
    user.is_active = False
    user.save()

    # 返回应答, 跳转到首页
    return redirect(reverse('goods:index'))


# 127.0.0.1:8000/user/register
class RegisterView(View):
    def get(self, request):
        """注册页面"""
        return render(request, 'register.html')

    def post(self, request):
        """注册业务逻辑处理"""
        # 接收数据
        username = request.POST.get('user_name')
        password = request.POST.get('pwd')
        email = request.POST.get('email')
        allow = request.POST.get('allow')

        # 验证数据
        if not all([username, password, email]):
            return render(request, 'register.html', {'err_msg': '数据不完整'})

        if not re.match(r'^[a-z0-9][\w.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
            return render(request, 'register.html', {'errmsg': '邮箱格式不正确'})

        if allow != 'on':
            return render(request, 'register.html', {'err_msg': '请同意协议'})

        try:
            user = User.objects.get(username=username)
        except Exception as e:
            user = None
        if user:
            return render(request, 'register.html', {'err_msg': '用户名已注册'})

        user = User.objects.create_user(username=username, password=password, email=email)
        # 是否激活修改为0
        user.is_active = False
        user.save()

        # 发送激活邮件，包含激活链接: http://127.0.0.1:8000/user/active/3
        # 激活链接中需要包含用户的身份信息, 并且要把身份信息进行加密

        # 加密用户的身份信息，生成激活token
        serializer = Serializer(settings.SECRET_KEY, 600)
        token = serializer.dumps({'confirm': user.id}).decode()

        # 发送邮件
        subject = '天天生鲜注册'
        message = ''
        sender = settings.SECRET_KEY
        from_email = [email]
        html_message = '<a href="127.0.0.1:8000/user/active/%s">127.0.0.1:8000/user/active/%s</a>'%(token, token)

        send_mail(subject, message, sender, from_email, html_message=html_message)
        # 返回应答, 跳转到首页
        return redirect(reverse('goods:index'))


# 127.0.0.1:8000/user/active/<id>
class ActiveView(View):
    """账号激活"""
    def get(self, request, token):
        serializer = Serializer(settings.SECRET_KEY, 600)
        try:
            info = serializer.loads(token)
            user_id = info['confirm']

            user = User.objects.get(id=user_id)
            user.is_active = 1
            user.save()

            # 激活成功，跳转到登陆界面
            return redirect(reverse('user:login'))

        except SignatureExpired as e:

            return HttpResponse("账户激活链接已过期")


# 127.0.0.1:8000/user/login
class LoginView(View):
    """登陆"""
    def get(self, request):
        """登陆界面"""
        # 是否记住了用户名
        if 'username' in request.COOKIES:
            username = request.COOKIES.get('username')
            checked = 'checked'
        else:
            username = ''
            checked = ''
        return render(request, 'login.html', locals())
