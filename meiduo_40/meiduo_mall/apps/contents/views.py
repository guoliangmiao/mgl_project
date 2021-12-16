from collections import OrderedDict

from django.shortcuts import render

# Create your views here.
from django.views import View

from apps.contents.utils import get_categories
from apps.goods.models import GoodsChannel

from apps.contents.models import ContentCategory
class IndexView(View):

    def get(self,request):

        # 1.查询商品频道和分类
        categories=get_categories()

        #2.广告楼层数据
        contents = {}
        #2.1先查询分类信息
        contents_categories=ContentCategory.objects.all()
        #2.2遍历
        for cat in contents_categories:
            contents[cat.key]=cat.content_set.filter(status=True).order_by('sequence')

        # 渲染模板的上下文
        context = {
            'categories': categories,
            'contents':contents
        }
        return render(request, 'index.html',context)



"""
1.首页经常被访问到,我们的数据经常被查询. 影响数据库的查询效率
2.首页数据经常发送变化

我们需要做的就是对首页进行静态化

静态化: 就是让用户去访问我们已经为他准备好的 html页面
定时任务:   让系统每间隔一定的时间去触发这个事件(函数)

"""