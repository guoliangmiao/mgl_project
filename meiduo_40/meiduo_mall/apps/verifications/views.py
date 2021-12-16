from django import http
from django.shortcuts import render

# Create your views here.
from django.views import View

from apps.verifications.constant import SMS_CODE_EXPIRE_TIME, YUNTONGXUN_EXPIRE_TIME
from libs.yuntongxun.sms import CCP
from utils.response_code import RETCODE
from redis import StrictRedis
"""
服务器
uuid_3:  1
uuid_4:  2
uuid_5:  4
杰哥:打款 100000000000000  10个亿

浏览器
uuid_3 借款1个
uuid_4 借款2个
uuid_5 借款4个

"""

"""
图片验证码的需求

前端需要生成一个uuid,这个uuid是可以确保在浏览器端唯一的,前端需要将uuid传递给后端

后端:
    路由和请求方式
    GET     提取URL的特定部分，如/weather/beijing/2018，可以在服务器端的路由中用正则表达式截取；
            image_codes/(?P<uuid>[\w-]+)/
            查询字符串（query string)，形如key1=value1&key2=value2
            verifications/?uuid=xxxx
    步骤
    1.接收这个uuid
    2.生成图片验证码,和保存图片验证码的内容
    3.把图片返回给浏览器
"""
from django.http import JsonResponse
import logging
logger = logging.getLogger('django')
class ImageCodeView(View):

    def get(self,request,uuid):
        # 1.接收这个uuid 已经获取了
        # uuid=request.GET.get('')
        # 2.生成图片验证码,和保存图片验证码的内容
            # 2.1 生成图片验证码,
        from libs.captcha.captcha import captcha
        # generate_captcha 它返回2个值,第一个值是 图片验证码的内容
        # 第二个值是图片验证码的二进制图片
        text,image = captcha.generate_captcha()

            # 2.2 保存图片验证码的内容 redis
        #2.2.1 连接redis
        from django_redis import get_redis_connection
        redis_conn = get_redis_connection('code')
        #2.2.2 保存数据
        # redis_conn.setex(键,过期时间,值)
        # redis_conn.setex(key,expire,value)
        redis_conn.setex('img_%s'%uuid,120,text)
        # 3.把图片返回给浏览器
        # application/json

        # content_type 其实就是MIME类型
        # 语法: 大类/小类
        # image 图片
        # image/jepg image/png image/gif
        # text/html     text/javascript     text/css

        # Content-Type:text/html 默认是 text/html
        # return http.HttpResponse(image)
        return http.HttpResponse(image,content_type='image/jpeg')

"""
SDK 理解为已经打包好的库
"""

class SMSCodeView(View):
    """
    需求：
        当用户输入完成手机号，图片验证码之后，点击获取短信验证码的时候，需要让前端提供
        手机号，图片验证码uuid，用户输入的图片验证码内容

    后端：
        请求方式和路由：
            GET
            提取URL的特定部分，如/weather/beijing/2018，可以在服务器端的路由中用正则表达式截取；

            查询字符串（query string)，形如key1=value1&key2=value2

            sms_codes/(?P<mobile>1[3-9]\d{9})/?uuid=xxx&text=xxx

            POST: 对于隐私性比较高的数据（例如密码）最好post
        步骤：
        1.后端要接收数据
        2.验证数据
            2.1 连接redis
            2.2 根据uuid获取redis中的数据
            2.3 redis中图片验证码有可能过期，判断是否过期
            2.4 比对
        3.生成短信验证码
        4.保存短信验证码
        5.发送短信验证码
        6.返回相应
    """
    def get(self,request,mobile):
        # 1.后端要接收数据
        params = request.GET
        uuid=params.get('image_code_id') #图片验证码的uuid
        text_client=params.get('image_code') #用户输入的图片验证码内容
        # 2.验证数据 比对 用户提交的图片验证码是否和redis中的一致
        # 2.1 连接redis
        from django_redis import get_redis_connection

        # 当我们去操作外界资源的时候,我们不能确定外界资源会发生什么问题
        # 所以我们需要对 操作外界资源的代码进行异常捕获 [mysql,Redis,读取文件]
        # 这样可以保证代码的健壮性
        try:
            redis_conn = get_redis_connection('code')
            # 2.2 根据uuid获取redis中的数据
            text_server=redis_conn.get('img_%s'%uuid)
            # 2.3 redis中图片验证码有可能过期，判断是否过期
            if text_server is None:
                return http.HttpResponseBadRequest('图片验证码已过期')
            # 2.4 比对
            # 从redis中获取的数据都是bytes类型
            if text_server.decode().lower() != text_client.lower():
                return http.HttpResponseBadRequest('图片验证码不一致')

            #2.5 删除redis中的已经获取的图片验证码内容
            redis_conn.delete('img_%s'%uuid)
        except Exception as e:
            logger.error(e)
            return http.HttpResponseBadRequest('数据库连接问题')

        # 先获取有没有标记位
        send_flag=redis_conn.get('send_flag_%s'%mobile)
        # redis获取的数据都是bytes类型
        if send_flag is not None:
            return http.HttpResponseBadRequest('操作太频繁了')


        # 3.生成短信验证码
        from random import randint
        # 12345
        # 123450
        sms_code = '%06d'%randint(0,999999)
        logger.info(sms_code)


        # 4.保存短信验证码
        # # redis_conn.setex(key,expires,value)
        # redis_conn.setex('sms_%s'%mobile,SMS_CODE_EXPIRE_TIME,sms_code)
        #
        # # 生成一个标记位 标记位为1  表示已经发送了
        # redis_conn.setex('send_flag_%s'%mobile,60,1)


        #4.1 通过redis的连接 创建管道实例
        pl=redis_conn.pipeline()
        #4.2 将redis指令 缓存在管道中
        # redis_conn.setex(key,expires,value)
        pl.setex('sms_%s' % mobile, SMS_CODE_EXPIRE_TIME, sms_code)

        # 生成一个标记位 标记位为1  表示已经发送了
        pl.setex('send_flag_%s' % mobile, 60, 1)
        #4.3 通过execute来执行管道
        pl.execute()

        """
        甲: 在吗?
        甲: 约吗?
        乙: 不约,


        优化:
        甲: 在吗?约吗?
        乙: 不约
        """

        # 5.发送短信验证码
        # send_template_sms 第一个参数： 给哪个手机发短信
        # 第二个参数： datas=[ 模板中的参数]  模板1中的短信验证码内容 模板1中的有效期（分钟数）
        # CCP().send_template_sms(mobile,[sms_code,YUNTONGXUN_EXPIRE_TIME],1)

        # 改为 celery
        from celery_tasks.sms.tasks import send_sms_code
        # delay 的参数 同 任务的参数
        send_sms_code.delay(mobile,sms_code)

        # 6.返回相应
        return http.JsonResponse({'code':RETCODE.OK})
