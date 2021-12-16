import re

from django import http
from django.contrib.auth import login
from django.shortcuts import render, redirect

# Create your views here.

#https://graph.qq.com/oauth2.0/authorize?response_type=code&client_id=101518219&redirect_uri=http://www.meiduo.site:8000/oauth_callback&state=lalalala

#http://路由/?key=value&key1=value1
# 我们的路由是 以? 为分割
# ?前边为请求的路由
# ?后边为请求的参数
from django.urls import reverse
from django.views import View
from django.http import JsonResponse
from QQLoginTool.QQtool import OAuthQQ
from django_redis import get_redis_connection

from apps.oauth.models import OAuthQQUser
from apps.oauth.utils import generic_openid_token, check_openid_token
from apps.users.models import User
from meiduo_mall import settings
from utils.response_code import RETCODE
import logging

logger = logging.getLogger('django')

class OauthQQURLView(View):

    def get(self,request):

        # 我给你 app_id redirect_uri
        # 你给我 一个跳转的url
        state=request.GET.get('next')
        #1.创建 OAuthQQ实例
        qq=OAuthQQ(
            client_id=settings.QQ_CLIENT_ID,
            redirect_uri=settings.QQ_REDIRECT_URI,
            client_secret=settings.QQ_CLIENT_SECRET,
            state=state
        )
        #2.调用实例方法
        login_url = qq.get_qq_url()

        # login_url = 'https://graph.qq.com/oauth2.0/show?which=Login&display=pc&response_type=code&client_id=101518219&redirect_uri=http://www.meiduo.site:8000/oauth_callback&state=test'

        return JsonResponse({'code':RETCODE.OK,'errmsg':'ok','ono':login_url})

"""
对于应用而言，需要进行两步：
1. 获取Authorization Code                           让用户登陆
2. 通过Authorization Code获取Access Token
"""
class OauthQQUserView(View):

    def get(self,request):
        """
        1.获取code(是用户同意登陆之后,qq服务器返回给我们的)
        2.通过code换取token(我们需要把code以及我们创建应用的serect 一并给qq服务器,qq服务器会认证
                            认证没有问题会返回给我们token)
        3.根据token换取openid (qq文档要求我们建立 openid和当前应用user的一对一关系)
        4.判断openid所对应的user信息是否存在
        5.如果不存在则进行绑定
        6.如果存在则进行登陆跳转

        """
        #1.获取code
        code = request.GET.get('code')
        if code is None:
            # return render()
            return http.HttpResponseBadRequest('参数有错误')
        #2.通过code换取token
        #https://graph.qq.com/oauth2.0/token?grant_type=authorization_code&client_id=101518219&client_secret=418d84ebdc7241efb79536886ae95224&redirect_uri=http://www.meiduo.site:8000/oauth_callback&code=D7C5A28379C019335C2596C14D72B43D

        # 2.1创建OAuthQQ实例
        qq = OAuthQQ(
            client_id=settings.QQ_CLIENT_ID,
            redirect_uri=settings.QQ_REDIRECT_URI,
            client_secret=settings.QQ_CLIENT_SECRET,
        )
        #2.2 通过code换取token
        token = qq.get_access_token(code)
        #'6734D20ADCF7BCD453098E282550A965'

        #3. 换取openid
        # https://graph.qq.com/oauth2.0/me?access_token=6734D20ADCF7BCD453098E282550A965
        openid = qq.get_open_id(token)
        #"openid":"64F0D4DAFC2444E0E61DA1323FE57188"

        # 4.判断openid所对应的user信息是否存在
        try:
            qquser = OAuthQQUser.objects.get(openid=openid)
        except OAuthQQUser.DoesNotExist:
            # 我需要对已一个openid进行加密处理
            openid_token = generic_openid_token(openid)
            # 5.如果不存在则进行绑定
            return render(request,'oauth_callback.html',context={'openid':openid_token})

        else:
            # 没有异常的时候走else
            # 6.如果存在则进行登陆跳转
            user = qquser.user
            # 6.1 保持登陆状态
            login(request,user)
            # 6.2 设置cookie
            next = request.GET.get('state')
            if next:
                response = redirect(next)
            else:
                response = redirect(reverse('contents:index'))
            response.set_cookie('username',user.username,max_age=14*24*3600)
            # 6.3 跳转
            return response

        # finally:
        #     # 什么时候都走
        #     pass


        return render(request,'oauth_callback.html')

    def post(self,request):
        """
        需求:
         当用户点击保存的时候,需要让前端将 openid_token,mobile,password,sms_code 提交给后端

         后端:

         大体步骤:
         1.接收数据
         2.验证数据
            手机号
            密码
            短信验证码
            openid_token
        3.绑定信息
            openid      是通过对oepnid_token的解密来获取
            user        需要根据 手机号进行判断
                            如果手机号注册,已经有user信息
                            如果没有注册,我们就创建一个user用户
        4.登陆状态保持
        5.cookie
        6.返回相应


        """
        #  1.接收数据
        data = request.POST
        mobile=data.get('mobile')
        password=data.get('password')
        sms_code_client = data.get('sms_code')
        access_token = data.get('access_token')
        #  2.验证数据
        if not all([mobile,password,sms_code_client]):
            # from django import http
            return http.HttpResponseBadRequest('参数不全')
        # ④验证用户名
        if not re.match(r'^1[3-9]\d{9}$',mobile):
            return http.HttpResponseBadRequest('手机号不满足条件')
        # ⑤验证密码
        if not re.match(r'^[0-9A-Za-z]{8,20}$',password):
            return http.HttpResponseBadRequest('密码格式不正确')
        #     短信验证码
        #  连接reids
        redis_conn = get_redis_connection('code')
        # 获取redis中的短信验证码
        sms_code_server = redis_conn.get('sms_%s' % mobile)
        #  判断redis中的短信验证码是否过期
        if not sms_code_server:
            return http.HttpResponseBadRequest('短信验证码已过期')
        #  比对
        if sms_code_server.decode() != sms_code_client:
            return http.HttpResponseBadRequest('短信验证码不一致')
        #     openid_token
        openid = check_openid_token(access_token)
        if openid is None:
            return http.HttpResponseBadRequest('openid错误')
        # 3.绑定信息
        #     openid      是通过对oepnid_token的解密来获取
        #     user        需要根据 手机号进行判断
        try:
            user = User.objects.get(mobile=mobile)
        except User.DoesNotExist:
            #                     如果没有注册,我们就创建一个user用户
            user = User.objects.create_user(
                username=mobile,
                password=password,
                mobile=mobile
            )
        else:
            #                     如果手机号注册,已经有user信息
            # 我们需要再次验证密码是否正确
            if not user.check_password(password):
                return http.HttpResponseBadRequest('密码错误')
        try:
            OAuthQQUser.objects.create(
                openid=openid,
                user=user
            )
        except Exception as e:
            logger.error(e)
            return http.HttpResponseBadRequest('数据库错误')

        # 4.登陆状态保持
        login(request,user)
        # 5.cookie
        response = redirect(reverse('contents:index'))

        response.set_cookie('username',user.username,max_age=14*24*3600)
        # 6.返回相应
        return response




###########################itsdangerous 加密######################################

from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from meiduo_mall import settings
#1.创建实例对象
#secret_key, expires_in
#secret_key         密钥      习惯上:使用setting中的SECRET_KEY
# expires_in        过期时间(单位:秒)
s = Serializer(settings.SECRET_KEY,300)
#2.组织数据
data = {'openid':'abcde'}
#3.加密处理
token = s.dumps(data)
# xxx.xxx.xx
#b'eyJhbGciOiJIUzUxMiIsImV4cCI6MTU1NzgwNjczNCwiaWF0IjoxNTU3ODA2NDM0fQ.eyJvcGVuaWQiOiJhYmNkZSJ9.6rv9GIO7Iw-weGiibDPOJrq4WdQ8NCO7PdKGUR1EhJ97_zwVGleESogPTpbXxAQk-f22rHcJ_FPM7QxoSoM4TA'
token.decode()

###############################itsdangerous 解密#####################################

from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from meiduo_mall import settings
#1.创建实例
s = Serializer(settings.SECRET_KEY,300)
#2.对数据进行解密
s.loads(token)
#{'openid': 'abcde'}

###############################itsdangerous 解密失败过期#####################################

from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from meiduo_mall import settings
#1.创建实例对象
#secret_key, expires_in
#secret_key         密钥      习惯上:使用setting中的SECRET_KEY
# expires_in        过期时间(单位:秒)
s = Serializer(settings.SECRET_KEY,1)
#2.组织数据
data = {'openid':'abcde'}
#3.加密处理
token = s.dumps(data)
# xxx.xxx.xx
#b'eyJhbGciOiJIUzUxMiIsImV4cCI6MTU1NzgwNjczNCwiaWF0IjoxNTU3ODA2NDM0fQ.eyJvcGVuaWQiOiJhYmNkZSJ9.6rv9GIO7Iw-weGiibDPOJrq4WdQ8NCO7PdKGUR1EhJ97_zwVGleESogPTpbXxAQk-f22rHcJ_FPM7QxoSoM4TA'
token.decode()

"""
Traceback (most recent call last):
  File "<console>", line 1, in <module>
  File "/home/python/.virtualenvs/py3_meiduo_mall_40/lib/python3.5/site-packages/itsdangerous/jws.py", line 205, in loads
    date_signed=self.get_issue_date(header),
itsdangerous.exc.SignatureExpired: Signature expired

"""

###############################itsdangerous 解密失败 数据被篡改#####################################

from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from meiduo_mall import settings
#1.创建实例对象
#secret_key, expires_in
#secret_key         密钥      习惯上:使用setting中的SECRET_KEY
# expires_in        过期时间(单位:秒)
s = Serializer(settings.SECRET_KEY,300)
#2.组织数据
data = {'openid':'abcde'}
#3.加密处理
token = s.dumps(data)
"""
s.loads('eyJhbGciOiJIUzUxMiIsImV4cCI6MTU1NzgwNzExNCwiaWF0IjoxNTU3ODA2ODE0fQ.eyJvcGVuaWQiOiJhYNkZSJ9.GRigrxTwflc74khO4LP0-VtxUeqxU0lXCdOLOv5jj3kZowTBW_SKWGUe0OzVTQPVQFDTGdxEtXyvRmJZA-ANQ')
Traceback (most recent call last):
  File "<console>", line 1, in <module>
  File "/home/python/.virtualenvs/py3_meiduo_mall_40/lib/python3.5/site-packages/itsdangerous/jws.py", line 187, in loads
    self, s, salt, return_header=True
  File "/home/python/.virtualenvs/py3_meiduo_mall_40/lib/python3.5/site-packages/itsdangerous/jws.py", line 143, in loads
    self.make_signer(salt, self.algorithm).unsign(want_bytes(s)),
  File "/home/python/.virtualenvs/py3_meiduo_mall_40/lib/python3.5/site-packages/itsdangerous/signer.py", line 169, in unsign
    raise BadSignature("Signature %r does not match" % sig, payload=value)
itsdangerous.exc.BadSignature: Signature b'GRigrxTwflc74khO4LP0-VtxUeqxU0lXCdOLOv5jj3kZowTBW_SKWGUe0OzVTQPVQFDTGdxEtXyvRmJZA-ANQ' does not match

"""