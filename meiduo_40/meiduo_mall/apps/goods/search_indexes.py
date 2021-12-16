"""
搜索

1.我们要运行搜索引擎
2.搜索引擎可以帮助我们对数据进行检索
3.我们需要借助于HayStack来实现和elasticsearch的交互



把数据给搜索引擎,搜索引擎会建立搜索的对应关系

我 是 中 国 人   --> 搜索引擎 --> 分词 --> 我,中国,中国人,国人,是中,人
I have a pen        I       Hava        a       pen
i have an apple

"""

from haystack import indexes
from apps.goods.models import SKU

class SKUIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    # text 是惯例命名
    # 每个都SearchIndex需要有一个（也是唯一一个）字段 document=True。
    # 这向Haystack和搜索引擎指示哪个字段是用于在其中搜索的主要字段

    # use_template
    #'name,id,caption'

    # 对哪个模型进行检索
    def get_model(self):
        return SKU

    # 对哪些数据进行检索
    def index_queryset(self, using=None):
        return self.get_model().objects.filter(is_launched=True)

# class OrderIndex(indexes.SearchIndex,indexes.Indexable):
#     abc = indexes.CharField(document=True)