from django import http
from django.core.cache import cache
from django.shortcuts import render

# Create your views here.
from django.views import View

from apps.areas.models import Area
from utils.response_code import RETCODE

"""
需求:
    1. 省的信息获取 ,市区县信息获取分开
    2. 当省的信息发生变化的时候,我们再获取 市/区县的信息
    3. 如何区分 省, 市/区县信息 就是通过前端传递过来的 area_id

后端:
    请求方式和路由
        GET     areas/?area_id=xxx

    大体步骤:
        1.接收area_id
        2.如果有area_id ,则查询 市/区县数据

        3.如果没有area_id ,则省的数据
            3.1.将对象列表转换为字典列表

优化:
    为什么要使用缓存?
        1.数据经常被访问到
        2.数据不经常(相对的)发生变化
    缓存的业务逻辑:

"""

class AreaView(View):

    def get(self,request):
        # 1.接收area_id
        area_id = request.GET.get('area_id')
        if area_id is not None:

            # 先从缓存中获取,获取之后进行判断
            sub_list = cache.get('sub_area_%s'%area_id)

            if sub_list is None:

                # 2.如果有area_id ,则查询 市/区县数据
                #2.1 根据area_id 获取市/区县信息
                areas = Area.objects.filter(parent_id=area_id)

                #2.2 对 对象列表进行转换来获取字典列表
                sub_list = []
                for area in areas:
                    sub_list.append({
                        'id':area.id,
                        'name':area.name
                    })

                # cache.set(key,value,expire)
                cache.set('sub_area_%s'%area_id,sub_list,24*3600)

            return http.JsonResponse({'code':RETCODE.OK,'errmsg':'ok','sub_list':sub_list})
        else:

            # 先查询缓存
            pro_list = cache.get('pro_list')
            # 如果缓存有,则直接使用缓存的
            if pro_list is None:
                # 3.如果没有area_id ,则省的数据
                areas = Area.objects.filter(parent=None)

                # 3.1.将对象列表转换为字典列表
                pro_list = []
                for area in areas:
                    pro_list.append({
                        'id':area.id,
                        'name':area.name
                    })


                # 把查询的数据放到缓存中
                # 1. 直接使用redis操作
                # 2. from django.core.cache import cache
                #       cache(key,value,expire)
                cache.set('pro_list',pro_list,24*3600)


            # 我们不能直接将对象列表/对象 传递给JsonRespnse
            # JsonResponse 只能返回 字典数据
            # 因为省,市区数据是局部刷新,所以我们采用ajax
            return http.JsonResponse({'code':RETCODE.OK,'errmsg':'ok','provinces':pro_list})


