"""
Django settings for meiduo_mall project.

Generated by 'django-admin startproject' using Django 1.11.11.

For more information on this file, see
https://docs.djangoproject.com/en/1.11/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.11/ref/settings/
"""
# 微信(电话):18310820688
# QQ:2860798672
# email: qiruihua@itcast.cn / qiruihua@live.cn
# git 网站:https://gitee.com/itcastitheima/meiduo_40.git

import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.11/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '6v6-nk1gh!alwi1zorjfbcvw_f+995gdxd9+)!lvrzprvz^7_*'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# 我们的域名 www.baidu.com 和IP 220.181.112.244 的对应关系
# 本机有记录,如果本机没有,会找远方的 DNS(记录ip和域名的关系)
# 在本机 添加一个  www.meiduo.site  和 127.0.0.1 的对应关系

# 允许,就是允许谁来访问我们的后台
# 这个是一个安全机制,默认只允许 127.0.0.1 来访问
# 如果你修改了一个允许访问的域名(ip),默认的127就不能访问了
ALLOWED_HOSTS = ['www.meiduo.site','127.0.0.1','192.168.229.148']


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # 注册子应用
    # 'apps.users.apps.UsersConfig'  = 'users' # 错误的
    # 我们注册子应用的本质其实就是引导到相应的子应用名就可以
    # 'users'
    'apps.users',                # 正确的
    'apps.contents',
    'apps.verifications',
    'apps.oauth',
    'apps.areas',
    'apps.goods',
    'apps.orders',
    'apps.payment',
    'haystack',
    'django_crontab',
]

CRONJOBS = [
    # 每1分钟生成一次首页静态文件
    # *分 *时 *日 *月 *周
    # 参数1: 频次
    # 参数2: 定时任务(函数)
    # 参数3: 日志

    ('*/1 * * * *', 'apps.contents.crons.generate_static_index_html', '>> ' + os.path.join(BASE_DIR, 'logs/crontab.log'))
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'meiduo_mall.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.jinja2.Jinja2',
        'DIRS': [os.path.join(BASE_DIR,'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
            #设置jiaji2环境
            'environment':'utils.jiaja2_env.jinja2_environment'
        },

    },
]

WSGI_APPLICATION = 'meiduo_mall.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.11/ref/settings/#databases

# 小型的:sqlite3

# mysql     : 甲骨文
# orical   :甲骨文
# sqlserver: 微软的
# DB2       : IBM

DATABASES = {
    'default': {
         'ENGINE': 'django.db.backends.mysql', # 数据库引擎
        'HOST': '127.0.0.1', # 数据库主机
        'PORT': 3306, # 数据库端口
        'USER': 'root', # 数据库用户名
        'PASSWORD': 'mysql', # 数据库用户密码
        'NAME': 'meiduo_mall_40' # 数据库名字
    },
    'slave': {
         'ENGINE': 'django.db.backends.mysql', # 数据库引擎
        'HOST': '127.0.0.1', # 数据库主机
        'PORT': 8306, # 数据库端口
        'USER': 'root', # 数据库用户名
        'PASSWORD': 'mysql', # 数据库用户密码
        'NAME': 'meiduo_mall_40' # 数据库名字
    },
}
DATABASE_ROUTERS = ['utils.db_router.MasterSlaveDBRouter']

# Redis
CACHES = {
    "default": {  # 预留,我们的省市区数据会放在0号库
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://127.0.0.1:6379/0",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        }
    },
    "session": { # 存放session数据
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://127.0.0.1:6379/1",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        }
    },
    "code": { # 图片验证码和短信的保存
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://127.0.0.1:6379/2",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        }
    },
    "history": { # 图片验证码和短信的保存
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://127.0.0.1:6379/3",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        }
    },
    "carts": { # 图片验证码和短信的保存
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://127.0.0.1:6379/4",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        }
    }
}
# 我们想把session信息 保存在redis中
SESSION_ENGINE = "django.contrib.sessions.backends.cache"
SESSION_CACHE_ALIAS = "session"


# Password validation
# https://docs.djangoproject.com/en/1.11/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/1.11/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.11/howto/static-files/

# 访问静态资源的url
STATIC_URL = '/static/'
# STATIC_ROOT = 'static_online'
# 访问静态资源的目录设置
STATICFILES_DIRS = [os.path.join(BASE_DIR,'static')]

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,  # 是否禁用已经存在的日志器
    'formatters': {  # 日志信息显示的格式
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(lineno)d %(message)s'
        },
        'simple': {
            'format': '%(levelname)s %(module)s %(lineno)d %(message)s'
        },
    },
    'filters': {  # 对日志进行过滤
        'require_debug_true': {  # django在debug模式下才输出日志
            '()': 'django.utils.log.RequireDebugTrue',
        },
    },
    'handlers': {  # 日志处理方法
        'console': {  # 向终端中输出日志
            'level': 'INFO',
            'filters': ['require_debug_true'],
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
        'file': {  # 向文件中输出日志
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(BASE_DIR, 'logs/meiduo.log'),  # 日志文件的位置
            'maxBytes': 300 * 1024 * 1024,
            'backupCount': 10,
            'formatter': 'verbose'
        },
    },
    'loggers': {  # 日志器
        'django': {  # 定义了一个名为django的日志器
            'handlers': ['console', 'file'],  # 可以同时向终端与文件中输出日志
            'propagate': True,  # 是否继续传递日志信息
            'level': 'INFO',  # 日志器接收的最低日志级别
        },
    }
}


# 我们需要用我们的User来替换系统的User
#https://yiyibooks.cn/xx/Django_1.11.6/topics/auth/customizing.html
# myapp.Myuser 注意点: 只能有一个点
# 系统是根据 . 来进行分割的
# myapp:子应用名
# MyUser: 模型类名
AUTH_USER_MODEL = 'users.User'

# 默认的认证后端
AUTHENTICATION_BACKENDS = [
     # 'django.contrib.auth.backends.ModelBackend',  #默认的认证后端
    'apps.users.utils.UsernameMobileModelBackend',
]

# 我们修改系统的默认的　未登录跳转路由
LOGIN_URL = '/login/'

#QQ登陆相关的
QQ_CLIENT_ID = '101518219'

QQ_CLIENT_SECRET = '418d84ebdc7241efb79536886ae95224'
# 回调的url 当用户点击同意登陆的时候,需要会跳到指定的页面
QQ_REDIRECT_URI = 'http://www.meiduo.site:8000/oauth_callback'

# 默认的发送邮件的后端
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
# 邮件服务器 因为我们是借助于 163.的 所有是 smtp.163.com
EMAIL_HOST = 'smtp.163.com'
#SMTP 的端口是固定的
EMAIL_PORT = 25
#发送邮件的邮箱 使用我的
EMAIL_HOST_USER = 'qi_rui_hua@163.com'
#在邮箱中设置的客户端授权密码
EMAIL_HOST_PASSWORD = '123456abc'

# 如果我们修改 确认邮箱的连接,则直接在setting中设置就好
EMAIL_VERIFY_URL = 'http://www.meiduo.site:8000/emails/verification/'


"""
Docker 是一个没有可视化界面的虚拟机
Docker 是C/S架构 我们需要按照Docker的客户端

镜像:
    我们可以理解为: 安装系统的镜像
    我们还可以理解为: 虚拟环境

容器:
    我们可以依赖于镜像创建很多个容器
    容器一般是2类:
        sudo docker run [选项] 镜像名   [指令]

        一类是交互方式  -i
            sudo docker run -it ubuntu
            sudo docker run -it ubuntu /bin/bash
            sudo docker run -it --name=myubuntu ubuntu
            --name 给容器起名字

        另外一类是守护[后台方式]进行方式 -d
            sudo docker run -dit ubuntu


    运行起来的镜像就叫容器 (容器需要依赖于 镜像)

仓库:
    类似于github 我们的镜像都存放在仓库中
    docker hub 中下载到本机

"""


# 指定自定义的Django文件存储类
DEFAULT_FILE_STORAGE = 'utils.fastdfs.storage.MyStorage'

FDFS_URL = 'http://192.168.229.148:8888/'

# haystack 和 搜索引擎 elasticsearch的对接配置
HAYSTACK_CONNECTIONS = {
    'default': {
        'ENGINE': 'haystack.backends.elasticsearch_backend.ElasticsearchSearchEngine',
        'URL': 'http://192.168.229.148:9200/',
        'INDEX_NAME': 'haystack',
    },
}

HAYSTACK_SEARCH_RESULTS_PER_PAGE = 5


ALIPAY_APPID = '2016091600523030'
ALIPAY_DEBUG = True
ALIPAY_URL = 'https://openapi.alipaydev.com/gateway.do'
ALIPAY_RETURN_URL = 'http://www.meiduo.site:8000/payment/status/'
APP_PRIVATE_KEY_PATH = os.path.join(BASE_DIR, 'apps/payment/keys/app_private_key.pem')
ALIPAY_PUBLIC_KEY_PATH = os.path.join(BASE_DIR, 'apps/payment/keys/alipay_public_key.pem')

"""
请求 --> Nginx --> 不擅长处理动态业务逻辑 --> uWSGI -->  Django -->视图


Nginx --> uWSGI --> Django

"""







