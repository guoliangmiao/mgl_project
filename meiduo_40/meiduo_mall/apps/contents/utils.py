from collections import OrderedDict

from apps.goods.models import GoodsChannel


# def get_categories():
#     categories = OrderedDict()
#     channels = GoodsChannel.objects.order_by('group_id', 'sequence')
#     for channel in channels:
#         group_id = channel.group_id  # 当前组
#
#         if group_id not in categories:
#             categories[group_id] = {'channels': [], 'sub_cats': []}
#
#         cat1 = channel.category  # 当前频道的类别
#
#         # 追加当前频道
#         categories[group_id]['channels'].append({
#             'id': cat1.id,
#             'name': cat1.name,
#             'url': channel.url
#         })
#         # 构建当前类别的子类别
#         for cat2 in cat1.subs.all():
#             cat2.sub_cats = []
#             for cat3 in cat2.subs.all():
#                 cat2.sub_cats.append(cat3)
#             categories[group_id]['sub_cats'].append(cat2)
#
#     return categories


def get_categories():

    #1.定义有序字典
    #2.查询所有的频道信息
    #3.对所有的频道进行遍历
    #4.获取当前频道的group_id(获取当前频道)
    #5.判断当前频道是否在有序字典中
    #6.获取当前的分类,将当前分类添加到频道中channels
    #7. 通过当前分类获取子分类以及子子分类添加到sub_cats中


    # 1.定义有序字典
    # {
    #   '1': {
    #       'channels':[],
    #        'sub_cats':[]
    #       }
    # }
    categories=OrderedDict()
    # 2.查询所有的频道信息
    channels=GoodsChannel.objects.all().order_by('group_id','sequence')

    # 3.对所有的频道进行遍历
    for channel in channels:

        # 4.获取当前频道的group_id(获取当前频道)
        group_id=channel.group_id

        # 5.判断当前频道是否在有序字典中
        if group_id not in categories:
            categories[group_id]={
                'channels':[],
                'sub_cats':[]
            }
        # 6.获取当前的分类,将当前分类添加到频道中channels
        category1=channel.category

        categories[group_id]['channels'].append({
            'id':category1.id,
            'name':category1.name,
            'url':channel.url
        })
        # 7. 通过当前分类获取子分类以及子子分类添加到sub_cats中
        for cat2 in category1.subs.all():
            cat2.sub_cats=[]
            for cat3 in cat2.subs.all():
                cat2.sub_cats.append(cat3)


            categories[group_id]['sub_cats'].append(cat2)


    return categories