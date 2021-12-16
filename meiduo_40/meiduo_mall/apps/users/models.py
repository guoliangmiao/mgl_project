from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.
"""
1.我们自己定义一个模型,模型中有三个字段就可以 用户名,密码,手机号
    密码加密的问题,密码验证的问题等等很多问题
2.系统的用户模型中 可以实现 密码加密的问题,密码验证的问题等等很多问题
    问题: 手机号没有

"""
# class User(models.Model):
#     username=models.CharField(max_length=20,unique=True,verbose_name='用户名')
#     password=models.CharField(max_length=20)

# 我们已经确定了让系统/用户 使用这个User
# 我们需要让我们的User来替换系统的User
#
class User(AbstractUser):
    mobile=models.CharField(max_length=11,unique=True,verbose_name='手机号')

    # False 为未激活(待验证)
    # True 已激活
    email_active=models.BooleanField(default=False,verbose_name='邮件激活状态')

    default_address = models.ForeignKey('Address', related_name='users', null=True, blank=True,
                                        on_delete=models.SET_NULL, verbose_name='默认地址')


    class Meta:
        db_table = 'tb_users'
        verbose_name = '用户'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.username


from utils.models import BaseModel

class Address(BaseModel):
    """用户地址"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='addresses', verbose_name='用户')
    title = models.CharField(max_length=20, verbose_name='地址名称')
    receiver = models.CharField(max_length=20, verbose_name='收货人')
    province = models.ForeignKey('areas.Area', on_delete=models.PROTECT, related_name='province_addresses', verbose_name='省')
    city = models.ForeignKey('areas.Area', on_delete=models.PROTECT, related_name='city_addresses', verbose_name='市')
    district = models.ForeignKey('areas.Area', on_delete=models.PROTECT, related_name='district_addresses', verbose_name='区')
    place = models.CharField(max_length=50, verbose_name='地址')
    mobile = models.CharField(max_length=11, verbose_name='手机')
    tel = models.CharField(max_length=20, null=True, blank=True, default='', verbose_name='固定电话')
    email = models.CharField(max_length=30, null=True, blank=True, default='', verbose_name='电子邮箱')
    is_deleted = models.BooleanField(default=False, verbose_name='逻辑删除')

    class Meta:
        db_table = 'tb_address'
        verbose_name = '用户地址'
        verbose_name_plural = verbose_name
        ordering = ['-update_time']
