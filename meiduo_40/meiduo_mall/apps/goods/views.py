from django import http
from django.shortcuts import render
from django.views import View

from apps.contents.utils import get_categories
from apps.goods.models import GoodsCategory, SKU
from apps.goods.utils import get_breadcrumb
from utils.response_code import RETCODE

"""
列表页面:
    有分类数据,面包屑(一级分类-->二级分类-->三级分类),列表数据,热销数据

    列表数据/热销数据其实是可以通过 ajax局部刷新的,但是由于我们讲的是前后端不分离
    所以我们把列表数据 放在我们查询之后,传递给模板,通过模板来渲染
"""

class ListView(View):
    """
    1.分类数据
    2.面包屑
    3.列表数据
    """
    def get(self,request,category_id,page_num):
        # 1.分类数据
        categories=get_categories()

        #2.获取面包屑数据
        # 面包屑数据其实就是分类数据
        # 当用户点击某一个分类的时候,就应该将这个分类id传递给我们
        try:
            # 获取的是三级分类
            category=GoodsCategory.objects.get(pk=category_id)
        except GoodsCategory.DoesNotExist:
            return http.HttpResponseBadRequest('分类错误')

        #因为面包屑在多个地方使用到了,所以就直接抽取
        breadcrumb=get_breadcrumb(category)

        #3.列表数据的获取
        #3.1获取所有数据(当前分类的)
        #3.2排序数据
        #先获取到查询字符串的 数据,
        # get(key,default_value)
        # 当获取值的时候,这个key所对应的为None的时候,则获取默认值
        sort=request.GET.get('sort','hot')
        # 再根据查询查询字符串的数据确定排序的字段
        if sort == 'default':
            sort_field='create_time'
        elif sort == 'price':
            sort_field='price'
        else:
            sort='hot'
            sort_field='-sales'

        skus=SKU.objects.filter(category=category).order_by(sort_field)
        #3.3 分页数据
        #导入分页类
        from django.core.paginator import Paginator
        # 创建分页类实例
        # object_list: 所有的数据
        # per_page: 每页多少条数据
        paginator=Paginator(skus,5)

        #获取当前页码所对应的数据
        try:
            # 对分页的数据进行一个类型转换
            page_num=int(page_num)
            page_skus = paginator.page(page_num)
        except Exception as e:
            pass

        #总页数
        total_page=paginator.num_pages

        context = {
            'categories':categories,
            'breadcrumb':breadcrumb,
            'category':category,
            'page_skus':page_skus,
            'total_page':total_page,
            'sort':sort,
            'page_num':page_num
        }
        return render(request,'list.html',context=context)

"""
热销数据的获取

需求:
    当用户点击了某一个分类之后,需要让前端将分类id传递给热销视图

后端:

    1.根据分类查询数据,进行排序,排序之后获取2条数据
    2.热销数据在某一段时间内 很少变化 可以做缓存

    路由和请求方式

    GET     hot/category_id/
"""
"""
从今天开始记一些相应状态码:
    200 成功

    300 重定向

    404 找不到页面(路由问题)
    403 Forbidden 禁止访问(权限问题/没有登陆)

    500 服务器问题(代码加断电)
"""
class HotView(View):

    def get(self,request,category_id):

        # SKU.objects.filter(category_id=category_id).order_by('-sales')[0:2]
        skus = SKU.objects.filter(category_id=category_id).order_by('-sales')[:2]

        #将对象列表转换为字典列表
        hot_skus = []
        for sku in skus:
            hot_skus.append({
                'id':sku.id,
                'price':sku.price,
                'default_image_url':sku.default_image.url,
                'name':sku.name
            })

        return http.JsonResponse({'code':RETCODE.OK,'errmsg':'ok','hot_skus':hot_skus})

class DetailView(View):
    """商品详情页"""

    def get(self, request, sku_id):
        """提供商品详情页"""
        # 获取当前sku的信息
        try:
            sku = SKU.objects.get(id=sku_id)
        except SKU.DoesNotExist:
            return render(request, '404.html')

        # 查询商品频道分类
        categories = get_categories()
        # 查询面包屑导航
        breadcrumb = get_breadcrumb(sku.category)

        # 构建当前商品的规格键
        sku_specs = sku.specs.order_by('spec_id')
        sku_key = []
        for spec in sku_specs:
            sku_key.append(spec.option.id)
        # 获取当前商品的所有SKU
        skus = sku.spu.sku_set.all()
        # 构建不同规格参数（选项）的sku字典
        spec_sku_map = {}
        for s in skus:
            # 获取sku的规格参数
            s_specs = s.specs.order_by('spec_id')
            # 用于形成规格参数-sku字典的键
            key = []
            for spec in s_specs:
                key.append(spec.option.id)
            # 向规格参数-sku字典添加记录
            spec_sku_map[tuple(key)] = s.id
        # 获取当前商品的规格信息
        goods_specs = sku.spu.specs.order_by('id')
        # 若当前sku的规格信息不完整，则不再继续
        if len(sku_key) < len(goods_specs):
            return
        for index, spec in enumerate(goods_specs):
            # 复制当前sku的规格键
            key = sku_key[:]
            # 该规格的选项
            spec_options = spec.options.all()
            for option in spec_options:
                # 在规格参数sku字典中查找符合当前规格的sku
                key[index] = option.id
                option.sku_id = spec_sku_map.get(tuple(key))
            spec.spec_options = spec_options


        # 渲染页面
        context = {
            'categories': categories,
            'breadcrumb': breadcrumb,
            'sku': sku,
            'specs':goods_specs
        }
        return render(request, 'detail.html',context=context)

"""
代码是具体的实例抽取出来的

"""


"""
需求:
    当用户点击详情(列表页面)页面的时候,我们需要让前端将分类id传递给后端
    后端对当前的分类数据进行+1的统计

后端:

    1.接收分类id
    2.查询对应的分类信息
    3.统计数据的更新
    4.返回数据

    请求方式和路由:
        post  detail/visit/(?P<category_id>\d+)/



"""
from apps.goods.models import GoodsVisitCount
class CategoryVisitView(View):

    def post(self,request,category_id):
        # 1.接收分类id
        # 2.查询对应的分类信息
        try:
            category=GoodsCategory.objects.get(pk=category_id)
        except GoodsCategory.DoesNotExist:
            return http.JsonResponse({'code':RETCODE.NODATAERR,'errmsg':'没有此分类'})
        # 3.统计数据的更新
        #3.1 先查询对应的当天和对应分类的记录
        # category
        # today 的日期
        from django.utils import timezone
        today=timezone.localdate()

        try:
            # gvc=GoodsVisitCount.objects.filter(category=category,date=today)[0]
            gvc=GoodsVisitCount.objects.get(category=category,date=today)
        except GoodsVisitCount.DoesNotExist:
            #查询不出来
            # 3.2 创建新的记录
            gvc=GoodsVisitCount(
                category=category,
                count=1,
                date=today
            )

            gvc.save()

        else:
            #查询出来了
            #3.3 更新数据
            gvc.count +=1
            gvc.save()



        # 4.返回数据
        return http.JsonResponse({'code':RETCODE.OK,'errmsg':'ok'})
