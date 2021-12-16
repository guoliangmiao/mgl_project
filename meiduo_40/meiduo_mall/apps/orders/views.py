import json

from decimal import Decimal
from django import http
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render

# Create your views here.
from django.views import View
from django_redis import get_redis_connection

from apps.goods.models import SKU
from apps.orders.models import OrderInfo, OrderGoods
from apps.users.models import Address
from utils.response_code import RETCODE
from utils.views import LoginRequiredJSONMixin

"""
订单结算页面的展示需求

    1.这个界面必须是登陆用户
    2.获取用户信息,
    3.根据用户信息,获取地址信息
    4.连接redis,获取redis中的 hash和set数据
        hash:
        set:
    5.将bytes数据类型进行转换,转换的同时我们重新组织选中的商品数据
        只有选中的 {sku_id:count}
    6.获取商品的id,根据商品id查询商品信息 [sku,sku]
    7.对商品列表进行遍历
    8.遍历的过程中 对sku添加数量和对应商品的总金额
        也去计算当前订单的总数量和总金额

"""

class PlaceOrderView(LoginRequiredMixin,View):

    def get(self,request):
        # 1.这个界面必须是登陆用户
        # 2.获取用户信息
        user=request.user
        # 3.根据用户信息,获取地址信息
        try:
            addresses=Address.objects.filter(user=user,is_deleted=False)
        except Exception as e:
            return http.HttpResponseNotFound('未找到数据')
        # 4.连接redis,获取redis中的 hash和set数据
        redis_conn = get_redis_connection('carts')
        #     hash  {sku_id:count}
        sku_id_count=redis_conn.hgetall('carts_%s'%user.id)
        #     set:
        ids=redis_conn.smembers('selected_%s'%user.id)

        # 5.将bytes数据类型进行转换,转换的同时我们重新组织选中的商品数据
        #     只有选中的 {sku_id:count}
        selected_carts={}
        for id in ids:
            selected_carts[int(id)]=int(sku_id_count[id])

        # 6.获取商品的id,根据商品id查询商品信息 [sku,sku]
        ids=selected_carts.keys()
        # [1,2,3]
        skus=SKU.objects.filter(pk__in=ids)
        # 7.对商品列表进行遍历
        total_count=0 #总数量
        from decimal import Decimal
        total_amount=Decimal('0') #总金额
        # 0.233333 小数是以无限接近于真实值形式存在的

        # 1000 / 3      333.33
        # 333.33*3 = 999.99
        # 333.33  333.33    333.34

        for sku in skus:
            # 8.遍历的过程中 对sku添加数量和对应商品的总金额
            sku.count=selected_carts[sku.id] #数量小计
            sku.amount=sku.count*sku.price                   #金额小计
            #     也去计算当前订单的总数量和总金额
            total_count += sku.count
            total_amount += sku.amount

        # 再添加一个运费信息
        freight=Decimal('10.00')


        context = {
            'addresses': addresses,
            'skus': skus,
            'total_count': total_count,
            'total_amount': total_amount,
            'freight': freight,
            'payment_amount': total_amount + freight
        }

        return render(request,'place_order.html',context=context)


# class Person(object):
#     name='itcast'
#
# p=Person()
# p.name
# p.age=14
# print(p.age)
#
# p2=Person()
# print(p2.age)

class OrderCommitView(LoginRequiredJSONMixin,View):

    """
    生成订单信息需要涉及到订单基本信息和订单商品信息,因为 订单基本信息订单商品信息
    是1对n,所以先生成1(订单基本信息)的数据,再生成订单商品

    1. 生成订单基本信息
        1.1 必须是登陆用户才可以访问.获取用户信息
        1.2 获取提交的地址信息
        1.3 获取提交的支付方式
        1.4 手动生成一个订单id 年月日时分秒+9位用户id
        1.5 运费,总金额和总数量(初始化为0)
        1.6 订单状态(由支付方式决定)
    2. 生成订单商品信息
        2.1 连接redis.获取redis中的数据
        2.2 获取选中商品的id [1,2,3]
        2.3 对id进行遍历
            2.4 查询商品
            2.5 库存量的判断
            2.6 修改商品的库存和销量
            2.7 累加总数量和总金额
            2.8 保存订单商品信息
            2.9 保存订单的总数量和总金额

    """
    def post(self,request):

        # 这里省略了很多增删改


        # 1. 生成订单基本信息
        #     1.1 必须是登陆用户才可以访问.获取用户信息
        user=request.user
        #     1.2 获取提交的地址信息
        data=json.loads(request.body.decode())
        address_id=data.get('address_id')
        try:
            address=Address.objects.get(pk=address_id)
        except Address.DoesNotExist:
            return http.JsonResponse({'code':RETCODE.PARAMERR,'errmsg':'参数错误'})
        #     1.3 获取提交的支付方式
        pay_method=data.get('pay_method')
        #最好对支付方式进行一个判断
        # 本质
        # if 1 in [1,2]:
        #     pass

        if not pay_method in [OrderInfo.PAY_METHODS_ENUM['CASH'],OrderInfo.PAY_METHODS_ENUM['ALIPAY']]:
            return http.JsonResponse({'code':RETCODE.PARAMERR,'errmsg':'参数错误'})

        #     1.4 手动生成一个订单id 年月日时分秒+9位用户id
        # Y Year
        # m month
        # d day
        # H Hour
        # M Minute
        # S Second
        from django.utils import timezone
        order_id=timezone.now().strftime('%Y%m%d%H%M%S') + '%09d'%user.id
        #     1.5 运费,总金额和总数量(初始化为0)
        freight=Decimal('10.00')  #运费
        total_amount=Decimal('0') #总金额
        total_count=0
        #     1.6 订单状态(由支付方式决定)
        # if pay_method == OrderInfo.PAY_METHODS_ENUM['CASH']:
        #     # 货到付款
        #     status=2
        # else:
        #     # 支付宝
        #     status=1

        if pay_method == OrderInfo.PAY_METHODS_ENUM['CASH']:
            # 货到付款
            status=OrderInfo.ORDER_STATUS_ENUM['UNSEND']
        else:
            # 支付宝
            status=OrderInfo.ORDER_STATUS_ENUM['UNPAID']

        from django.db import transaction
        with transaction.atomic():

            #1.创建事务回滚的点
            save_point=transaction.savepoint()

            order=OrderInfo.objects.create(
                order_id=order_id,
                user=user,
                address=address,
                total_count=total_count,
                total_amount=total_amount,
                freight=freight,
                pay_method=pay_method,
                status=status
            )



            # 2. 生成订单商品信息
            #     2.1 连接redis.获取redis中的数据 选中的商品的信息{sku_id:count}
            redis_conn=get_redis_connection('carts')
            id_count=redis_conn.hgetall('carts_%s'%user.id)
            selected_ids=redis_conn.smembers('selected_%s'%user.id)

            selected_carts={}
            for id in selected_ids:
                selected_carts[int(id)]=int(id_count[id])
            #     2.2 获取选中商品的id [1,2,3]
            ids=selected_carts.keys()
            #     2.3 对id进行遍历
            for id in ids:
                while True:
                    #         2.4 查询商品
                    sku=SKU.objects.get(pk=id)
                    #         2.5 库存量的判断
                    count=selected_carts[sku.id]
                    if sku.stock<count:
                        #出现问题进行回滚
                        transaction.savepoint_rollback(save_point)
                        #说明库存不足
                        return http.JsonResponse({'code':RETCODE.STOCKERR,'errmsg':'库存不足'})
                    #         2.6 修改商品的库存和销量
                    # import time
                    # time.sleep(7)

                    # sku.stock-=count
                    # sku.sales+=count
                    # sku.save()

                    #乐观锁
                    # 先添加(修改)事务的隔离界别
                    # transaction-isolation=READ-COMMITTED
                    #2.6.1 先获取之前的库存
                    old_stock=sku.stock  #5

                    #2.6.2 新库存和新销量
                    new_stock=sku.stock-count
                    new_sales=sku.sales+count
                    #2.6.3
                    rect=SKU.objects.filter(id=id,stock=old_stock).update(
                        stock=new_stock,
                        sales=new_sales
                    )

                    if rect == 0:
                        continue
                        #表示失败
                        # transaction.savepoint_rollback(save_point)
                        # return http.JsonResponse({'code':RETCODE.STOCKERR,'errmsg':'下单失败'})
                        # raise Exception('下单失败~~~~~')
                    # else:
                    #     print('lalalalal ok~~~~~')
                    #
                    #         2.7 累加总数量和总金额
                    order.total_count+=count
                    order.total_amount+=(sku.price*count)
                    #         2.8 保存订单商品信息
                    OrderGoods.objects.create(
                        order=order,
                        sku=sku,
                        count=count,
                        price=sku.price
                    )

                    break

            # 3.保存订单的总数量和总金额
            order.save()

            #3.提交
            transaction.savepoint_commit(save_point)

        #4.删除redis中选中的商品信息


        return http.JsonResponse({'code':RETCODE.OK,'errmsg':'ok','order_id': order.order_id})




    """
        A   15      B 15
    甲
        买   A10    B10

    乙
         买  A10    B10

     甲 A 锁  等着B锁开了再加锁

     乙 B 锁  等A开锁

    乐观锁
    乐观锁并不是真实存在的锁，而是在更新的时候判断此时的库存是否是之前查询出的库存，
    如果相同，表示没人修改，可以更新库存，否则表示别人抢过资源，不再执行库存更新

    肉包子 100     50

    甲 100      100-50=50
    乙 100      50

    """


class OrderSuccessView(LoginRequiredMixin,View):

    def get(self,request):
        order_id = request.GET.get('order_id')
        payment_amount = request.GET.get('payment_amount')
        pay_method = request.GET.get('pay_method')

        context = {
            'order_id': order_id,
            'payment_amount': payment_amount,
            'pay_method': pay_method
        }

        return render(request,'order_success.html',context=context)