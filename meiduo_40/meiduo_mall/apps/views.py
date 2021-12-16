from django.http import HttpResponse

#1.导入
import logging
#2.创建(获取)日志实例
logger = logging.getLogger('django')

def log(request):

    #3.记录日志
    logger.info('~~~~~~~lalalalala')
    logger.error('error')
    logger.debug('ooooooo')

    return HttpResponse('log')