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
import base64
import pickle

from django_redis import get_redis_connection


def merge_cookie_to_redis(request,user,response):
    # 1.获取到cookie数据
    carts=request.COOKIES.get('carts')
    if carts is not None:
        cookie_cart=pickle.loads(base64.b64decode(carts))
        # {
        #  1:{count:15,selected:True},
        #         2:{count:200,selected:False}
        # }

        # {sku_id:count}
        cookie_hash={}
        #选中的id
        cookie_selected_ids=[]
        #未选中的id
        cookie_unselected_ids=[]
        # 2.遍历cookie数据
        for sku_id,count_selected_dict in cookie_cart.items():

            # 3.当前是以cookie为主,所以我们直接将cookie数据转换为hash, set(记录选中的和未选中的)
            cookie_hash[sku_id]=count_selected_dict['count']

            if count_selected_dict['selected']:
                cookie_selected_ids.append(sku_id)
            else:
                cookie_unselected_ids.append(sku_id)



        # 4.连接redis 更新redis数据
        redis_conn = get_redis_connection('carts')
        #hash {sku_id:count}
        # user=request.user
        redis_conn.hmset('carts_%s'%user.id,cookie_hash)
        # set
        # 选中的ids
        # [1,2]
        if cookie_selected_ids:
            redis_conn.sadd('selected_%s'%user.id,*cookie_selected_ids)

        # 未选中的 ids 从选中的集合中移除
        if cookie_unselected_ids:
            redis_conn.srem('selected_%s'%user.id,*cookie_unselected_ids)
        # 5.将cookie数据删除
        response.delete_cookie('carts')


        return response


    return response


"""

将抽象的问题具体化

斐波那契数列

已知数列的第1项和第2项分别为1, 从第3项等于第2项加第1项,第4项等于第3项加第2项

第n项=第n-1项+第n-2项


    1
    1
1+1=2
2+1=3
3+2=5
5+3=8
8+5=13
...

"""

def abc(n):

    if n==1:
        return 1
    if n==2:
        return 1

    return abc(n-1)+abc(n-2)


abc(4)