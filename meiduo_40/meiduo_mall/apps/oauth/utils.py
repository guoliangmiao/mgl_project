from itsdangerous import TimedJSONWebSignatureSerializer as Serializer

from apps.oauth.constants import OPENID_TOKEN_EXPIRES_TIME
from meiduo_mall import settings
import logging
logger = logging.getLogger('django')

def generic_openid_token(openid):
    #1.创建实例对象
    # s = Serializer(secret_key=settings.SECRET_KEY,expires_in=300)
    s = Serializer(secret_key=settings.SECRET_KEY,expires_in=OPENID_TOKEN_EXPIRES_TIME)
    #2.组织数据
    data = {
        'openid':openid
    }
    #3.加密数据
    token = s.dumps(data)
    #4.返回数据
    return token.decode()
from itsdangerous import SignatureExpired,BadData
def check_openid_token(token):

    #1. 创建实例
    s = Serializer(secret_key=settings.SECRET_KEY, expires_in=OPENID_TOKEN_EXPIRES_TIME)
    #2.解密,解密的时候要捕获异常
    try:
        result = s.loads(token)
        # result = {}
    # except Exception as e:
    #     return None
    except BadData as e:
        logger.error(e)
        return None
    #3.获取解密之后的数据
    return result.get('openid')
