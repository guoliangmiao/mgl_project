"""
Celery 将三者串联起来

生成者
    1.需要单独创建一个任务包,任务包中的py文件必须以 tasks.py作为我们的文件名
    2.生成者/任务 其本质就是 函数
    3.这个函数必须要经过 celery的实例对象的task装饰器装饰
    4.这个任务需要让celery自动检测
消息队列

消费者
    语法:celery -A proj worker -l info
    语法:celery -A celery实例对象的文件 worker -l info
    需要在虚拟环境中执行: celery -A celery_tasks.main
"""

#1.导入celery
from celery import Celery

#2.先进行配置
# 让celery 去加载有可能用到的django的配置文件
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "meiduo_mall.settings")

#3.创建celery实例对象
# main 一般习惯性 将工程的名字作为它的参数值,确保 celery实例唯一就可以
app = Celery('celery_tasks')

#4.配置 消息队列(broker)
# broker 可以实现消息队列的功能
#Redis
# 我们需要让celery加载[配置信息
# config_from_object 直接写配置文件的路径
app.config_from_object('celery_tasks.config')


#5.让celery自动检测任务
# autodiscover_tasks(列表)
# 列表的元素: 任务包的路径
app.autodiscover_tasks(['celery_tasks.sms','celery_tasks.email'])

