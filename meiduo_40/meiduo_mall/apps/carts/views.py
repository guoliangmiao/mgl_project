import base64
import json
import pickle

from django import http
from django.shortcuts import render

# Create your views here.
from django.views import View
from django_redis import get_redis_connection

from apps.goods.models import SKU
from utils.response_code import RETCODE

"""
分析:
    方向一: 通过经验
    方向二: 看别的网站的类似的效果


需求:

   1. 未登录用户可以实现购物车的添加,也能够保存数据

        登陆用户可以实现购物车的添加

    2.未登录用户保存在哪里  浏览器 (cookie中)

        登录用户保存在哪里  服务器  数据库中
                                Redis(课程设计,真实实现)

    3. 未登录用户保存 商品id,商品数量,勾选状态
        cookie:
        key:value
        carts: { sku_id: {count:xxx,selected:True} }


        carts: {
                    1:{count:5,selected:True},
                    3:{count:15,selected:False},
                }

        登录用户保存 用户id,商品id,商品数量,勾选状态

            数据库 user_id,sku_id,count,selected

                     1      1       5   1
                     1      3       15  0
                     333    1       1   1
                     333    2       1   0



            Redis(课程设计,真实实现)
            Redis是保存在内存中,我们的原则是:尽量少的占用内存空间 (先实现功能)

                 user_id,sku_id,count,selected



            Hash
                user_id:
                        sku_id:count,
                        sku_id:count,

                1:
                  1:10


                  2:20


                2:
                  1:10


                  2:20
            Set
                user_id: [sku_id,sku_id] 选中的商品的id

                1:  [1]

                2:


    4. 对cookie数据进行加密处理

        1G=1024MB
        1M=1024KB
        1KB=1024B
        1B=8bytes

        1字节=8b
        b: 0/1

        A       0100    0001

        A   A   A
        0100    0001    0100    0001    0100    0001

        X   y z s
        010000      010100    000101    000001

"""




class CartsView(View):
    """
    添加购物车的思路

        需求:
            当用户点击加入购物车的时候,需要让前端收集  sku_id,count,selected(可以不提交默认是True)
            因为请求的时候会携带用户信息(如果用户登陆)
        后端:

            # 1.后端接收数据
            # 2.验证数据
            # 3.判断用户登陆状态
            # 4.登陆用户保存在redis
            #     4.1 连接redis
            #     4.2 hash
            #         set
            #     4.3 返回
            # 5.未登录用户保存在cookie中
            #     5.1 组织数据
            #     5.2 加密
            #     5.3 设置cookie
            #     5.4 返回相应

        路由和请求方式
            POST        carts
    """
    def post(self,request):
        # 1.后端接收数据
        data=json.loads(request.body.decode())
        # 2.验证数据
        sku_id=data.get('sku_id')
        count=data.get('count')
        selected=data.get('selected',True)

        #2.1 商品id,个数必须传递
        if not all([sku_id,count]):
            return http.JsonResponse({'code':RETCODE.PARAMERR,'errmsg':'参数不全'})
        #2.2 判断商品是否存在
        try:
            sku=SKU.objects.get(pk=sku_id)
        except SKU.DoesNotExist:
            return http.JsonResponse({'code':RETCODE.NODATAERR,'errmsg':'没有此商品'})
        #2.3 判断商品的个数是否为整形
        try:
            count=int(count)
        except Exception as e:
            return http.JsonResponse({'code':RETCODE.PARAMERR,'errmsg':'参数错误'})
        #2.4 判断选中状态是否为bool值
        if not isinstance(selected,bool):
            return http.JsonResponse({'code': RETCODE.PARAMERR, 'errmsg': '参数错误'})
        # 3.判断用户登陆状态
        user = request.user
        if user.is_authenticated:
            # 4.登陆用户保存在redis
            #     4.1 连接redis
            redis_conn = get_redis_connection('carts')
            #     4.2 hash
            # carts_userid:
            #   sku_id:count
            # redis_conn.hset(key,field,value)
            # redis_conn.hset('carts_%s'%user.id,sku_id,count)
            redis_conn.hincrby('carts_%s'%user.id,sku_id,count)
            #         set 集合
            redis_conn.sadd('selected_%s'%user.id,sku_id)
            #     4.3 返回
            return http.JsonResponse({'code':RETCODE.OK,'errmsg':'ok'})

        else:
            # 5.未登录用户保存在cookie中
            """
            carts: {
                sku_id:{count:xxx,selected:xxx}
            }
            """
            #     5.1 先读取cookie数据,判断cookie数据中,
            # 是否存在carts数据
            carts=request.COOKIES.get('carts')
            if carts is not None:
                # 如果存在,则需要对数据进行解密
                # 先将base64的数据解密为bytes
                decode = base64.b64decode(carts)
                # 再将bytes类型的数据转换为字典
                cookie_cart=pickle.loads(decode)

            else:
                # 如果不存在,则初始化字典
                cookie_cart = {}

            # 判断sku_id 是否存在于cookie_cart
            # 在里边则累加
            """
            carts: {
                sku_id:{count:xxx,selected:xxx}
            }
            """
            if sku_id in cookie_cart:
                #先把原数据获取到
                orginal_count=cookie_cart[sku_id]['count']
                #再累加
                # count=count+orginal_count
                count += orginal_count

            #再更新数据
            cookie_cart[sku_id]={
                'count':count,
                'selected':selected
            }
            #     5.2 加密
            # 5.2.1 将字典转换为 bytes类型
            dumps = pickle.dumps(cookie_cart)
            #5.2.2 将bytes类型进行base64加密
            cookie_data = base64.b64encode(dumps)
            #     5.3 设置cookie
            response = http.JsonResponse({'code':RETCODE.OK,'errmsg':'ok'})


            response.set_cookie('carts',cookie_data.decode(),max_age=3600)
            #     5.4 返回相应

            return response


    """
    前端根据用户的状态,登陆就传递用户信息,不登陆就不传用户信息

    1.判断用户是否登陆
    2.登陆用户到redis中获取数据
        2.1 连接redis
        2.2 获取数据 hash   carts_userid: {sku_id:count}
                    set     selected: [sku_id,]
        2.3 获取所有的商品id
        2.4 根据商品id查询商品的详细信息 [sku,sku,sku]
        2.5 将对象转换为字典
    3.未登录用户到cookie中获取数据
        3.1 获取cookie中carts数据,同时进行判断
        3.2 carts: {sku_id:{count:xxx,selected:xxx}}
        3.3 获取所有商品的id
        3.4 根据商品id查询商品的详细信息 [sku,sku,sku]
        3.5 将对象转换为字典


    1.判断用户是否登陆
    2.登陆用户到redis中获取数据
        2.1 连接redis
        2.2 获取数据 hash   carts_userid: {sku_id:count}
                    set     selected: [sku_id,]

    3.未登录用户到cookie中获取数据
        3.1 获取cookie中carts数据,同时进行判断
        3.2 carts: {sku_id:{count:xxx,selected:xxx}}


    4 获取所有商品的id
    5 根据商品id查询商品的详细信息 [sku,sku,sku]
    6 将对象转换为字典
    7 返回相应
    """
    def get(self,request):
        # 1.判断用户是否登陆
        user=request.user
        if user.is_authenticated:
            # 2.登陆用户到redis中获取数据
            #     2.1 连接redis
            redis_conn = get_redis_connection('carts')
            #     2.2 获取数据 hash   carts_userid: {sku_id:count}
            sku_id_count=redis_conn.hgetall('carts_%s'%user.id)
            #                 set     selected: [sku_id,]
            # [1,2,3]
            selected_ids=redis_conn.smembers('selected_%s'%user.id)


            #因为 redis和cookie的数据格式不一致,我们需要转换数据
            # 将redis转换为cookie的格式
            # carts: {sku_id:{count:xxx,selected:xxx}}
            cookie_cart = {}

            for sku_id,count in  sku_id_count.items():

                # 判断我们遍历的商品id,是否在选中的列表中
                if sku_id in selected_ids:
                    selected=True
                else:
                    selected=False

                cookie_cart[int(sku_id)]={
                    'count':int(count),
                    # 'selected':sku_id in selected_ids
                    'selected':selected
                }

        else:
            # 3.未登录用户到cookie中获取数据
            carts=request.COOKIES.get('carts')
            #     3.1 获取cookie中carts数据,同时进行判断
            if carts is not None:
                #有数据
                decode=base64.b64decode(carts)
                cookie_cart= pickle.loads(decode)
            else:
                #没有数据
                cookie_cart={}
            #    carts: {sku_id:{count:xxx,selected:xxx}}

        # carts: {sku_id:{count:xxx,selected:xxx}}
        # 4 获取所有商品的id
        ids = cookie_cart.keys()
        # 5 根据商品id查询商品的详细信息 [sku,sku,sku]
        # Decimal
        # mysql: float,double,decimal(货比类型)
        skus=[]
        for id in ids:
            sku=SKU.objects.get(pk=id)
            # 6 将对象转换为字典
            skus.append({
                'id':sku.id,
                'name':sku.name,
                'count': cookie_cart.get(sku.id).get('count'),
                'selected': str(cookie_cart.get(sku.id).get('selected')),  # 将True，转'True'，方便json解析
                'default_image_url':sku.default_image.url,
                'price':str(sku.price), # 从Decimal('10.2')中取出'10.2'，方便json解析
                'amount':str(sku.price * cookie_cart.get(sku.id).get('count')),
            })
        context = {
            'cart_skus': skus,
        }

        # 渲染购物车页面
        return render(request, 'cart.html', context)

    """
    1.接收数据
    2.验证数据
    3.获取用户用户信息,根据用户信息进行判断
    4.登陆用户redis
    5.未登录用户cookie


    1.接收数据
    2.验证数据
        2.0 sku_id,selected,count 都要提交过来
        2.1 验证商品id
        2.2 验证商品数量
        2.3 验证选中状态是否为bool
    3.获取用户用户信息,根据用户信息进行判断
    4.登陆用户redis
        4.1 连接redis
        4.2 更新数据
        4.3 返回相应
    5.未登录用户cookie
        5.1 获取cookie中的carts数据
        5.2 判断数据是否存在
        5.3 更新数据
        5.4 对新数据进行加密处理
        5.5 返回相应

    """
    def put(self,request):
        # 1.接收数据
        data=json.loads(request.body.decode())

        sku_id = data.get('sku_id')
        count = data.get('count')
        selected = data.get('selected', True)

        # 2.1 商品id,个数必须传递
        if not all([sku_id, count,selected]):
            return http.JsonResponse({'code': RETCODE.PARAMERR, 'errmsg': '参数不全'})
        # 2.2 判断商品是否存在
        try:
            sku = SKU.objects.get(pk=sku_id)
        except SKU.DoesNotExist:
            return http.JsonResponse({'code': RETCODE.NODATAERR, 'errmsg': '没有此商品'})
        # 2.3 判断商品的个数是否为整形
        try:
            count = int(count)
        except Exception as e:
            return http.JsonResponse({'code': RETCODE.PARAMERR, 'errmsg': '参数错误'})
        # 2.4 判断选中状态是否为bool值
        if not isinstance(selected, bool):
            return http.JsonResponse({'code': RETCODE.PARAMERR, 'errmsg': '参数错误'})
        # 3.判断用户登陆状态
        user=request.user
        if user.is_authenticated:
            # 4.登陆用户redis
            #     4.1 连接redis
            redis_conn = get_redis_connection('carts')
            #     4.2 更新数据
            # hash
            redis_conn.hset('carts_%s'%user.id,sku_id,count)
            # set
            if selected:
                redis_conn.sadd('selected_%s'%user.id,sku_id)
            else:
                redis_conn.srem('selected_%s'%user.id,sku_id)
            #     4.3 返回相应
            cart_sku = {
                'id': sku_id,
                'count': count,
                'selected': selected,
                'name': sku.name,
                'default_image_url': sku.default_image.url,
                'price': sku.price,
                'amount': sku.price * count,
            }
            return http.JsonResponse({'code':RETCODE.OK,'errmsg':'ok','cart_sku':cart_sku})

        else:
            # 5.未登录用户cookie
            #     5.1 获取cookie中的carts数据
            carts=request.COOKIES.get('carts')
            #     5.2 判断数据是否存在
            if carts is not None:
                #存在,解密
                cookie_cart=pickle.loads(base64.b64decode(carts))
            else:
                #不存在
                cookie_cart={}
            #     5.3 更新数据
            # {sku_id:{count:xxx,selected:xxxx}}
            if sku_id in cookie_cart:
                cookie_cart[sku_id]={
                    'count':count,
                    'selected':selected
                }
                #     5.4 对新数据进行加密处理
                cookie_data=base64.b64encode(pickle.dumps(cookie_cart))
            #     5.5 返回相应
            cart_sku = {
                'id': sku_id,
                'count': count,
                'selected': selected,
                'name': sku.name,
                'default_image_url': sku.default_image.url,
                'price': sku.price,
                'amount': sku.price * count,
            }
            response = http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'ok', 'cart_sku': cart_sku})

            response.set_cookie('carts',cookie_data.decode(),3600)

            return response

    """
    1.接收数据(sku_id)
    2.验证数据(验证商品是否存在)
    3.获取用户信息
    4.登陆用户操作redis
        4.1 连接redis
        4.2 删除数据 hash,set
        4.3 返回相应
    5.未登录用户操作cookie
        5.1 获取carts数据
        5.2 判断数据是否存在
        5.3 删除数据
        5.4 对最新的数据进行加密处理
        5.5 返回相应
    """
    def delete(self,request):
        # 1.接收数据(sku_id)
        data=json.loads(request.body.decode())
        sku_id=data.get('sku_id')
        # 2.验证数据(验证商品是否存在)
        try:
            sku=SKU.objects.get(pk=sku_id)
        except SKU.DoesNotExist:
            return http.JsonResponse({'code':RETCODE.NODATAERR,'errmsg':'无此数据'})
        # 3.获取用户信息
        user=request.user
        if user.is_authenticated:
            # 4.登陆用户操作redis
            #     4.1 连接redis
            redis_conn = get_redis_connection('carts')
            #     4.2 删除数据 hash,set
            # hash
            redis_conn.hdel('carts_%s'%user.id,sku_id)
            #set
            redis_conn.srem('selected_%s'%user.id,sku_id)
            #     4.3 返回相应
            return http.JsonResponse({'code':RETCODE.OK,'errmsg':'ok'})

        else:
            # 5.未登录用户操作cookie
            #     5.1 获取carts数据
            carts=request.COOKIES.get('carts')
            #     5.2 判断数据是否存在
            if carts is not None:
                # 有数据
                cookie_cart=pickle.loads(base64.b64decode(carts))
            else:
                #没有数据
                cookie_cart={}
            #     5.3 删除数据
            if sku_id in cookie_cart:
                del cookie_cart[sku_id]
            #     5.4 对最新的数据进行加密处理
            cookie_data=base64.b64encode(pickle.dumps(cookie_cart))
            #     5.5 返回相应
            response=http.JsonResponse({'code':RETCODE.OK,'errmsg':'ok'})

            response.set_cookie('carts',cookie_data,3600)

            return response

"""

将抽象的问题具体化

需求:
    当用户登陆的时候,需要将cookie数据合并到reids中

    1.用户登陆的时候
    2.合并数据

    将cookie数据合并到reids中
    1.获取到cookie数据
    2.遍历cookie数据
    3.当前是以cookie为主,所以我们直接将cookie数据转换为hash, set(记录选中的和未选中的)

    4.连接redis 更新redis数据
    5.将cookie数据删除

将抽象的问题具体化

Redis
    hash:   user_id:
                            1:10
                            3:20
    set selected_user_id    1

Cookie
        {
                1:{count:15,selected:True},
                2:{count:200,selected:False}
        }

将cookie数据进行合并,如果商品id冲突(cookie中有,redis中)
        数量是以redis为主
        数量是以cookie为主        v
        数量是以累加为主

    1:{count:15,selected:True},
    2:{count:200,selected:False}

    hash  {1:15,2:200}
    set    [1]
"""