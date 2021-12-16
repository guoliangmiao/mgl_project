import json
import re
from django import http
from django.contrib.auth import login
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views import View
# Create your views here.
from django_redis import get_redis_connection

from apps.carts.utils import merge_cookie_to_redis
from apps.goods.models import SKU
from apps.users.models import User, Address

#1.导入
import logging
#2.创建(获取)日志实例
from apps.users.utils import generic_verify_email_url, check_veryfy_email_token
from utils.response_code import RETCODE
from utils.views import LoginRequiredJSONMixin

logger = logging.getLogger('django')

"""
功能点如何分析:
    1.需要依靠经验
    2.看其他网站的类似功能
注册页面的功能点:
    1.用户名:
        不能重复
        有长度限制
    2.密码:
        有长度限制
        数字和字母
    3.确认密码:
        需要和密码一致
    4.手机号
        符合要求
        不能重复
    5.图片验证码
        后台实现
        作用: 区分人和计算机的
        服务于: 短信验证码(发送短信花钱)
    6.短信验证码
        后台实现
        发送短信前先验证 图片验证码
    7.用户点击注册按钮的时候
        必须保存: 用户名,密码和手机号
        原因: 我们在登陆的时候需要使用这三个字段
    8.同意按钮
        需要点击同意

需求分析分析出来之后:
    1.先分析模型
    2.再众多功能中,找一个功能来入手,不要考虑很多的功能点(哪个简单,会哪个就先做哪个)
    3.把最难的功能放在最后
"""

"""
具体需求:
    当用户点击注册按钮的时候,需要让前端将 用户名,密码,确认密码,手机号,是否同意协议 提交给后台

后台:
    1.先确定路由和提交方式: POST      register/

        提取URL的特定部分，如/weather/beijing/2018，可以在服务器端的路由中用正则表达式截取；
        register/itcast/1234567890/1234567890/18212345678/on/

        查询字符串（query string)，形如key1=value1&key2=value2；
        register?itcast/1234567890/1234567890/18212345678/on/

        请求体（body）中发送的数据，比如表单数据、json、xml

    2.根据需求把大体步骤写下来[后端不相信前端提交的任何数据]
        ①接收数据
        ②验证数据
        ③保存数据
        ④返回相应

    3.具体实现的思路(步骤)
        ①接收数据 request.POST
        ②分别获取数据 username,password
        ③判断要求的数据是否齐全 [少参数就没有必要继续验证了]
        ④验证用户名
        ⑤验证密码
        ⑥验证确认密码
        ⑦验证手机号
        ⑧验证是否同意协议
        ⑨保存数据
        ⑩跳转首页,返回相应

    4.添加断点
        在函数的入库处,添加
     作用:
        ① 查看程序运行过程中的变量数据
        ② 一步一步的来梳理业务逻辑
        ③ 当我们验证某一行代码的时候可以添加断点
"""
class RegisterView(View):

    def get(self,request):

        return render(request,'register.html')

    def post(self,request):
        # ①接收数据 request.POST
        data=request.POST
        # ②分别获取数据 username,password
        username=data.get('username')
        password=data.get('password')
        password2=data.get('password2')
        mobile=data.get('mobile')
        allow=data.get('allow')
        sms_code_client=data.get('sms_code')
        # ③判断要求的数据是否齐全 [少参数就没有必要继续验证了]
        # all([username,password,password2,mobile,allow])
        # 只要列表中的数据有一个为 None 则返回False
        if not all([username,password,password2,mobile,allow,sms_code_client]):
            # from django import http
            return http.HttpResponseBadRequest('参数不全')
        # ④验证用户名
        if not re.match(r'^[0-9a-zA-Z_-]{5,20}$',username):
            return http.HttpResponseBadRequest('用户名不满足条件')
        # ⑤验证密码
        if not re.match(r'^[0-9A-Za-z]{8,20}$',password):
            return http.HttpResponseBadRequest('密码格式不正确')
        # ⑥验证确认密码
        if password2!=password:
            return http.HttpResponseBadRequest('密码不一致')
        # ⑦验证手机号
        if not re.match(r'^1[3-9]\d{9}$',mobile):
            return http.HttpResponseBadRequest('手机号不符合规则')
        # ⑧验证是否同意协议
        if allow != 'on':
            return http.HttpResponseBadRequest('您未同意协议')

        # 8.1 验证 用户提交的短信验证码和redis的短信验证码是否一致
        # 8.1.1 连接reids
        redis_conn = get_redis_connection('code')
        #.8.1.2 获取redis中的短信验证码
        sms_code_server=redis_conn.get('sms_%s'%mobile)
        # 8.1.3 判断redis中的短信验证码是否过期
        if not sms_code_server:
            return http.HttpResponseBadRequest('短信验证码已过期')
        # 8.1.4 比对
        if sms_code_server.decode() != sms_code_client:
            return http.HttpResponseBadRequest('短信验证码不一致')

        # ⑨保存数据,我们要把数据保存在数据库中
        try:
            # create_user 是系统提供的 自动对密码进行加密的方法,同时也会会创建用户
            user = User.objects.create_user(
                username=username,
                password=password,
                mobile=mobile
            )
        except Exception as e:
            logger.error(e)
            return render(request,'register.html',context={'register_errmsg':'创建用户失败'})
        """
        注册: 不同的产品需求是不一样的
            有的是 跳转到首页 v  默认登陆  应该有session信息
            有的是 跳转到登陆页面
        """

        # 设置登陆信息(session)
        from django.contrib.auth import login
        login(request,user)

        # ⑩跳转首页,返回相应
        # reverse(name)
        # reverse(namespace:name)
        return redirect(reverse('contents:index'))
        # return http.HttpResponse('ok')

class RegisterUsernameCountView(View):
    """
    1. 需求:
        当用户输入在输入用户名之后,光标失去焦点之后,前端应该发送一个ajax请求
        这个ajax请求 需要包含一个参数 username
    2.后台
        ① 确定请求方式和路由
            提取URL的特定部分，如/weather/beijing/2018，可以在服务器端的路由中用正则表达式截取；
            查询字符串（query string)，形如key1=value1&key2=value2

            GET  路由   usernames/(?P<username>[a-zA-Z0-9_]{5,20})/
                        register/count/?username=username
        ② 大体步骤写下来
            一.参数校验(已经在路由中做过了)
            二.根据用户名进行查询
            三.返回相应
    """

    def get(self,request,username):
        # 一.参数校验(已经在路由中做过了)
        # if not re.match(r'')
        # 二.根据用户名进行查询
        # filter() 返回的是一个列表
        count = User.objects.filter(username=username).count()
        # User.objects.filter(username__exact=username)
        # 三.返回相应
        return http.JsonResponse({'count':count})

class LoginView(View):
    """
    需求:
        当用户将用户名和密码填写完成之后,前端需要将用户名和密码发送给后端
    后台:
        请求方式和路由
            POST  login/
        大体步骤
            1.接收数据
            2.获取数据
            3.验证是否齐全(用户名和密码都要传递过来)
            4.判断用户名是否符合规则
            5.判断密码是否符合规则
            6.验证用户 用户名和密码是否正确
            7.保持会话
            8.返回相应
    """

    def get(self,request):
        return render(request,'login.html')

    def post(self,request):
        # 1.接收数据
        data = request.POST
        # 2.获取数据
        username=data.get('username')
        password=data.get('password')
        remembered=data.get('remembered')

        # 3.验证是否齐全(用户名和密码都要传递过来)
        if not all([username,password]):
            return http.HttpResponseBadRequest('参数不齐')
        # 4.判断用户名是否符合规则
        if not re.match(r'^[0-9a-zA-Z_-]{5,20}$', username):
            return http.HttpResponseBadRequest('用户名不满足条件')
        # 5.判断密码是否符合规则
        if not re.match(r'^[0-9A-Za-z]{8,20}$', password):
            return http.HttpResponseBadRequest('密码格式不正确')
        # 6.验证用户 用户名和密码是否正确
        # ① 我们可以根据用户进行查询,再判断密码
        # ② 采用系统自带的认证
        from django.contrib.auth import authenticate
        #authenticate(username=xx,password=xxx)
        # 如果我们传递的用户名和密码都正确,它会返回 我们user对象
        # 如果我们传递的用户名/密码不正确,它不会返回我们user信息
        user = authenticate(username=username,password=password)

        if user is None:
            return render(request,'login.html',{'login_error_message':'用户名或密码错误'})
        # 7.保持会话
        login(request,user)

        # 添加记住登陆/不记住登陆的功能
        if remembered != 'on':
            #说明不需要记住
            request.session.set_expiry(0)
        else:
            # 需要记住
            request.session.set_expiry(None)

        #request.user.is_authenticated
        # is_authenticated 判断用户是否登陆
        # 如果登陆返回true
        # 如果没有登陆返回false

        # 先获取 next参数
        # http://www.meiduo.site:8000/login/?next=/info/
        next = request.GET.get('next')
        if next:
            response = redirect(next)
        else:
            # 8.返回相应 设置cookie
            response = redirect(reverse('contents:index'))

        # 设置cookie信息
        # response.set_cookie(key,value,max_age=)
        if remembered != 'on':
            #说明不需要记住
            # response.set_cookie('username', user.username, max_age=None)
            response.set_cookie('username', user.username)
        else:
            # 需要记住
            response.set_cookie('username', user.username, max_age=14*24*3600)


        # 在这里合并
        response = merge_cookie_to_redis(request,user,response)

        return response

from django.contrib.auth import logout

class LogoutView(View):

    # ctrl+k 弹出 git 提示框 (前提是 需要在setting中 将本工程 添加git管理)
    #ｃｔrl+shirt+k 可以ｐｕｓｈ

    def get(self,request):
        """
        1.调用系统的退出方法(系统的退出方法原理: 删除session是信息)
        2.把cookie信息(username)清除一下 因为我们的首页是通过username来判断是否登陆的
        3.跳转页面
        """
        logout(request)

        response = redirect(reverse('contents:index'))

        # 清除cookie数据
        # response.set_cookie()
        response.delete_cookie('username')

        return response

#django自带了认证的一个方法，可以判断　用户是否登陆了
from django.contrib.auth.mixins import LoginRequiredMixin

class UserInfoView(LoginRequiredMixin,View):
    # 必须是登陆用户才可以访问
    # 如果用户没有登陆，默认会调转到系统的　登陆路由
    #系统的默认登陆路由是：/accounts/login/
    #
    def get(self,request):

        #1.获取指定的数据组织上下文
        context = {
            'username':request.user.username,
            'mobile':request.user.mobile,
            'email':request.user.email,
            'email_active':request.user.email_active
        }

        return render(request,'user_center_info.html',context=context)

"""
需求(用户做了什么,我们要做什么[ 需要让前端提交什么,我们后端接收什么]):
    当用户在邮件输入框中,输入一个邮件之后,点击保存的时候,需要让前端将邮箱信息发送给后端
后端

    确定请求方式和路由:
        put         /emails/
    大体步骤:
        1.必须是登陆用户才可以更新邮箱信息
        2.接收用户提交的邮箱信息
        3.验证邮箱信息是否符合邮箱规则
        4.保存数据
        5.发送激活邮件
        6.返回相应


    GET     :       获取数据
    POST    :       新增数据
    PUT     :       更新数据/修改数据  put和post是类似的 我们的请求数据是请求的body中
    DELETE  :       删除数据
"""

# LoginRequiredMixin 会进行一个重定向
# 我们这里是进行的ajax 请求,我们应该返回一个json数据
from django.contrib.auth.mixins import LoginRequiredMixin

class EmailView(LoginRequiredJSONMixin,View):

    def put(self,request):
        # 1.必须是登陆用户才可以更新邮箱信息
        # if request.user.is_authenticated

        # 2.接收用户提交的邮箱信息
        # data = request.POST

        #1.1.获取body数据
        body=request.body
        #1.2.body数据是bytes类型,进行类型转换
        body_str=body.decode()
        #1.3.对字符串JSON,进行转换
        data = json.loads(body_str)

        email = data.get('email')
        # 3.验证邮箱信息是否符合邮箱规则
        if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$',email):
            return http.JsonResponse({'code':RETCODE.PARAMERR,'errmsg':'参数错误'})
        # 4.更新数据
        try:
            request.user.email=email
            request.user.save()
        except Exception as e:
            logger.error(e)
            return http.JsonResponse({'code':RETCODE.DBERR,'ermsg':'更新错误'})
        # 5.发送激活邮件
        from django.core.mail import send_mail
        #subject, message, from_email, recipient_list,
        #subject,               主题
        subject='美多商城激活邮件'
        # message,              消息
        message=''
        # from_email,           谁发的邮件
        from_email='美多商城<qi_rui_hua@163.com>'
        # recipient_list,       收件人列表 []
        recipient_list = [email]

        # html_message = "<a href='#'>戳我,戳我,戳我有惊喜</a>"
        # 激活的url中包含 用户的信息就可以

        verify_url = generic_verify_email_url(request.user.id)

        html_message = '<p>尊敬的用户您好！</p>' \
                   '<p>感谢您使用美多商城。</p>' \
                   '<p>您的邮箱为：%s 。请点击此链接激活您的邮箱：</p>' \
                   '<p><a href="%s">%s<a></p>' % (email, verify_url, verify_url)
        # send_mail(
        #     subject=subject,
        #     message=message,
        #     from_email=from_email,
        #     recipient_list=recipient_list,
        #     html_message=html_message
        # )
        from django.core.mail import send_mail
        from celery_tasks.email.tasks import send_verify_email
        send_verify_email.delay(
            subject=subject,
            message=message,
            from_email=from_email,
            recipient_list=recipient_list,
            html_message=html_message)
        # 6.返回相应
        return http.JsonResponse({'code':RETCODE.OK,'errmsg':'ok'})



"""
需求:
    当用户点击激活连接的时候,可以展示该页面,同时,获取前端提交过来的token
后端:

    请求方式和路由:
        GET     emails/verification

    1.接收token
    2.验证token
    3.根据user_id查询用户信息
    4.改变用户信息
    5.返回相应(跳转到个人中心页面)
"""

class EmailVerifyView(View):

    def get(self,request):
        # 1.接收token
        token = request.GET.get('token')
        if token is None:
            return http.HttpResponseBadRequest('参数错误')
        # 2.验证token
        user_id = check_veryfy_email_token(token)
        if user_id is None:
            return http.HttpResponseBadRequest('参数错误')
        # 3.根据user_id查询用户信息
        try:
            # pk primary key 主键的意思
            # 如果我们不记得主键是哪个字段的时候,可以直接使用pk
            # 系统会自动使用主键
            # user = User.objects.get(id=user_id)
            user = User.objects.get(pk=user_id)
            # 4.改变用户信息
            if user is not None:
                user.email_active=True
                user.save()
        except User.DoesNotExist:
            return http.HttpResponseBadRequest('参数错误')
        # 5.返回相应(跳转到个人中心页面)
        return redirect(reverse('users:info'))


class AddressView(LoginRequiredMixin,View):

    def get(self,request):

        """
        1.必须是登陆用户
        2.查询登陆用户的地址信息 [Address,Address]
        3.对列表数据进行转换为字典列表
        4.传递给模板
        """
        # 2.查询登陆用户的地址信息 [Address,Address]
        addresses = Address.objects.filter(user=request.user,is_deleted=False)
        # 3.对列表数据进行转换为字典列表
        addresses_list = []
        for address in addresses:
            addresses_list.append({
                "id": address.id,
                "title": address.title,
                "receiver": address.receiver,
                "province": address.province.name,
                "province_id": address.province_id,
                "city": address.city.name,
                "city_id": address.city_id,
                "district": address.district.name,
                "district_id": address.district_id,
                "place": address.place,
                "mobile": address.mobile,
                "tel": address.tel,
                "email": address.email
            })
        # 4.传递给模板
        context = {
            'addresses':addresses_list,
            'default_address_id':request.user.default_address_id

        }
        return render(request,'user_center_site.html',context=context)


class CreateAddressView(LoginRequiredJSONMixin,View):
    """
    需求:
        当用户填写完新增数据之后,点击新增按钮,需要让前端将 收货人等信息提交给后端

    后端:

        大体步骤:
        1.判断当前用户是否登陆
        2.接收参数
        3.验证参数
        4.数据入库
        5.返回相应

        请求方式和路由:
            POST    /addresses/create/
    """

    def post(self,request):

        #0 判断用户的地址数量是否超过20个
        count = Address.objects.filter(user=request.user,is_deleted=False).count()
        if count > 20:
            return http.JsonResponse({'code':RETCODE.THROTTLINGERR,'errmsg':'个数超过上限'})

        # 1.判断当前用户是否登陆
        # if request.user.is_authenticated

        # 2.接收参数
        json_dict = json.loads(request.body.decode())
        receiver = json_dict.get('receiver')
        province_id = json_dict.get('province_id')
        city_id = json_dict.get('city_id')
        district_id = json_dict.get('district_id')
        place = json_dict.get('place')
        mobile = json_dict.get('mobile')
        tel = json_dict.get('tel')
        email = json_dict.get('email')

        # 校验参数
        if not all([receiver, province_id, city_id, district_id, place, mobile]):
            return http.HttpResponseBadRequest('缺少必传参数')
        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return http.HttpResponseBadRequest('参数mobile有误')
        if tel:
            if not re.match(r'^(0[0-9]{2,3}-)?([2-9][0-9]{6,7})+(-[0-9]{1,4})?$', tel):
                return http.HttpResponseBadRequest('参数tel有误')
        if email:
            if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
                return http.HttpResponseBadRequest('参数email有误')
        # 4.数据入库
        try:
            address = Address.objects.create(
                user=request.user,
                title=receiver,
                receiver=receiver,
                province_id=province_id,
                city_id=city_id,
                district_id=district_id,
                place=place,
                mobile=mobile,
                tel=tel,
                email=email
            )

            # 如果没有默认地址我们就设置一个默认地址
            if not request.user.default_address:
                request.user.default_address=address
                request.user.save()

        except Exception as e:
            logger.error(e)
            return http.JsonResponse({'code':RETCODE.DBERR,'errmsg':'数据库操作失败'})
        # 5.返回相应
        # 新增地址成功，将新增的地址响应给前端实现局部刷新
        address_dict = {
            "id": address.id,
            "title": address.title,
            "receiver": address.receiver,
            "province": address.province.name,
            "city": address.city.name,
            "district": address.district.name,
            "place": address.place,
            "mobile": address.mobile,
            "tel": address.tel,
            "email": address.email
        }
        return http.JsonResponse({'code':RETCODE.OK,'errmsg':'ok','address':address_dict})


class UpdateDestoryAddressView(LoginRequiredJSONMixin,View):
    """
    需求: 当用户修改了地址信息之后,需要让前端将 这个信息全都收集过去
    后端:

        1.判断用户是否登陆
        2.根据传递过来的更新指定的地址信息
        3.更新
        4.返回相应

    请求方式和路由
        PUT addresses/id/
    """
    def put(self,request,address_id):
        json_dict = json.loads(request.body.decode())
        receiver = json_dict.get('receiver')
        province_id = json_dict.get('province_id')
        city_id = json_dict.get('city_id')
        district_id = json_dict.get('district_id')
        place = json_dict.get('place')
        mobile = json_dict.get('mobile')
        tel = json_dict.get('tel')
        email = json_dict.get('email')

        # 2.根据传递过来的更新指定的地址信息
        # address = Address.objects.get(pk=address_id)
        # address.recever=data.get('recever')
        # 3.更新
        try:
            # 更新成功之后,返回 1 表示更新成功
            # 返回 0 表示更新失败

            Address.objects.filter(pk=address_id).update(
                user=request.user,
                title=receiver,
                receiver=receiver,
                province_id=province_id,
                city_id=city_id,
                district_id=district_id,
                place=place,
                mobile=mobile,
                tel=tel,
                email=email
            )
            # 再次查询一下地址信息
            address = Address.objects.get(pk=address_id)
        except Exception as e:
            logger.error(e)
            return http.JsonResponse({'code':RETCODE.DBERR})

        # 4.返回相应
        address_dict = {
            "id": address.id,
            "title": address.title,
            "receiver": address.receiver,
            "province": address.province.name,
            "city": address.city.name,
            "district": address.district.name,
            "place": address.place,
            "mobile": address.mobile,
            "tel": address.tel,
            "email": address.email
        }
        return http.JsonResponse({'address':address_dict,'code':RETCODE.OK})

    def delete(self,request,address_id):
        try:
            address = Address.objects.get(pk=address_id)

            # address.delete()
            address.is_deleted=True
            address.save()
        except Exception as e:
            pass

        return http.JsonResponse({'code':RETCODE.OK})


"""
用户id,商品id

Redis

    String      key:value

    Hash
                key:
                    field:value
                    field:value

                user_id:
                    field:sku_id
    List
                key: [value1,value2,value1]

                user_id:[sku_id,sku_id]  有顺序,不能去重,去重需要我们自己实现
    Set(集合)    不重复,没有顺序
                key: member,member
                user_id:[value2,value1]
    Zset(有序集合) 不会重复,有顺序
                key: member,member

                user_id: [value1,value2,value3]


"""

"""
添加用户浏览记录的
需求

    当登陆用户访问某一个商品详情页面的时候,需要让前端发送一个ajax请求,将用户信息和sku_id
    发送给后端
 后端:

    1.接收数据
    2.判断验证数据
    3.数据入库(redis)
    4.返回相应

    请求方式和路由
    POST    browse_histories/
"""

class HistoryView(LoginRequiredJSONMixin,View):

    def post(self,request):
        # 1.接收数据
        user=request.user

        data=json.loads(request.body.decode())
        sku_id=data.get('sku_id')
        # 2.判断验证数据
        try:
            sku=SKU.objects.get(pk=sku_id)
        except SKU.DoesNotExist:
            return http.JsonResponse({"code":RETCODE.NODATAERR,'errmsg':'暂无此商品'})
        # 3.数据入库(redis)
        redis_conn = get_redis_connection('history')
        pl=redis_conn.pipeline()
        # 分析的时候 是可以将数据保存为 有序集合的 有序集合的score是时间戳(秒数)
        # 分析的时候 也可以用 列表
        # 去重, 有顺序

        # 3.1 先去重 通过 lrem 找到和当前value一样的数据,先删除
        # redis_conn.lrem(key,count,value)
        pl.lrem('history_%s'%user.id,0,sku_id)
        #3.2 从左边添加
        pl.lpush('history_%s'%user.id,sku_id)
        #3.3 对列表进行裁剪

        pl.ltrim('history_%s'%user.id,0,4)

        pl.execute()

        # 4.返回相应
        return http.JsonResponse({'code':RETCODE.OK,'errmsg':'ok'})



    def get(self,request):
        """
        1.获取用户信息
        2.连接redis.获取用户信息 [1,2,3,4,]
        3.对id列表进行遍历来获取详细信息
            根据id进行查询,
            将对象转换为字典
        4.返回数据
        """
        # 1.获取用户信息
        user = request.user
        # 2.连接redis.获取用户信息 [1,2,3,4,]
        redis_conn =get_redis_connection('history')
        ids = redis_conn.lrange('history_%s'%user.id,0,4)
        # [1,2,3,4]
        # 3.对id列表进行遍历来获取详细信息
        skus=[]
        for sku_id in ids:

            #     根据id进行查询
            sku = SKU.objects.get(pk=sku_id)
            #     将对象转换为字典
            skus.append({
                'id': sku.id,
                'name': sku.name,
                'default_image_url': sku.default_image.url,
                'price': sku.price
            })
        # 4.返回数据
        return http.JsonResponse({'code':RETCODE.OK,'errmsg':'ok','skus':skus})














"""
增
    1.接收数据
    2.验证数据
    3.数据入库
    4.返回相应
删
    1.根据id进行查询
    2.删除就行
改
    1.先接收要修改哪个数据(根据id进行查询)
    2.接收修改之后的数据
    3.验证数据
    4.更新数据(保存数据)
    5.返回相应
查
    1.根据已知条件进行查询
    2.查询出来的是对象列表,我们需要将对象列表转换为字典
    3.返回数据

"""


class Person(object):

    name = ''
    sex = ''

p = Person()
p.name='itcast'


p2 = Person()
p2.name='itheima'


class Phone(object):

    color=''
    price=''


phonex_blue = Phone()
phonex_blue.color=''
phonex_blue.price=''
"""
1:1     一个表  或者是2个表
                    个人信息(常用信息)      个人信息(不常用)

1:n     2表
                    用户:订单表
                    商品:图片
n:m     3个表
                    供应商:产品
                    老师:学生

设置模型的要求:
    资深工程师
    18K
"""