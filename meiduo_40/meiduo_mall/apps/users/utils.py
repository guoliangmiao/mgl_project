import re

from django.contrib.auth.backends import ModelBackend

from apps.users.models import User

"""
1. 我们需要的需求是 用户名或手机号登陆,系统默认提供的是 用户名登陆
    当系统的类/方法 不能我们我们需求的时候,我们就继承重写
2. 代码的抽取/封装(思想)

    ① 为什么要抽取代码
        减低代码的耦合度
        代码的复用(多个地方使用,如果有需求的变更,我们只该一个地方)
    ② 我什么时候抽取代码
        某些行(1,n行)代码实现了一个小的功能
        当你复制重复(第二个复制的)代码的时候就要考虑是否抽取
    ③ 如何实现呢?
        先定义一个函数(方法),函数名无所谓,也不用关系参数
        将要抽取的代码拷贝到这个函数中,哪里有问题改哪里,没有的变量以参数的形式传递
        验证,验证没有问题之后,再将原代码删除
"""

def get_user_by_username(username):
    try:
        if re.match(r'1[3-9]\d{9}', username):
            # 手机号
            user = User.objects.get(mobile=username)
        else:
            # 用户名
            user = User.objects.get(username=username)
    except User.DoesNotExist:
        return None
    # 记得返回user
    return user

class UsernameMobileModelBackend(ModelBackend):

    def authenticate(self, request, username=None, password=None, **kwargs):

        # username 有可能是 用户名 也有可能是手机号
        #  如果是用户名 itcast        我们查询的时候应该是根据用户名进行查询
        #  如果是手机号  13812345678  我们查询的时候应该是根据手机号进行查询
        # 根据正则来区分手机号
        # 1.需要区分 用户名和手机号 查询出用户
        # try:
        #     if re.match(r'1[3-9]\d{9}',username):
        #         #手机号
        #         user=User.objects.get(mobile=username)
        #     else:
        #         #用户名
        #         user=User.objects.get(username=username)
        # except User.DoesNotExist:
        #     return None

        user = get_user_by_username(username)
        # 2.根据用户的信息来验证密码
        if user is not None and user.check_password(password):
            return user


from itsdangerous import TimedJSONWebSignatureSerializer as Serializer,SignatureExpired,BadData

from meiduo_mall import settings
def generic_verify_email_url(user_id):

    #1.创建实例对象
    s = Serializer(secret_key=settings.SECRET_KEY,expires_in=3600)
    #2.组织数据
    data = {
        'user_id':user_id
    }
    #3.加密数据
    token = s.dumps(data)
    #4.返回数据
    return  settings.EMAIL_VERIFY_URL + '?token=' + token.decode()

def check_veryfy_email_token(token):

    #1.创建实例对象
    s = Serializer(secret_key=settings.SECRET_KEY, expires_in=3600)
    #2.对数据进行解密,解密的时候可能有异常
    try:
        result = s.loads(token)
    except BadData:
        return None
    #3.返回数据
    return result.get('user_id')
