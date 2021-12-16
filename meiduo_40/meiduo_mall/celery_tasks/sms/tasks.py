# 1.需要单独创建一个任务包,任务包中的py文件必须以 tasks.py作为我们的文件名
# 2.生成者/任务 其本质就是 函数
# 3.这个函数必须要经过 celery的实例对象的task装饰器装饰
# 4.这个任务需要让celery自动检测
from apps.verifications.constant import YUNTONGXUN_EXPIRE_TIME
from libs.yuntongxun.sms import CCP
from celery_tasks.main import app

import logging
logger = logging.getLogger('django')

# bind=True 是表示把任务自己传递过去,这样我们就可以在任务的第一个参数中,传递self
# 函数中的 self 就是 Task(任务)本身
@app.task(bind=True,default_retry_delay=5,name='send_sms')
def send_sms_code(self,mobile,sms_code):
    try:
        result = CCP().send_template_sms(mobile, [sms_code, YUNTONGXUN_EXPIRE_TIME], 1)
        if result != 0:
            raise Exception('下单失败')
    except Exception as exc:
        logger.error(exc)
        # max_retries 设置最大的重试次数
        raise self.retry(exc=exc,max_retries=3)
