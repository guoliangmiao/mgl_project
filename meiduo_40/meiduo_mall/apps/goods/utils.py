
# def get_breadcrumb(cat):
#     # cat 传递过来的是一个 三级分类
#
#     # 组织面包屑数据
#     """
#     {
#         cat1:一级分类内容,
#         cat2:二级分类内容,
#         cat3:三级分类内容
#     }
#     """
#
#     return {
#         'cat1':cat.parent.parent,
#         'cat2':cat.parent,
#         'cat3':cat
#     }

def get_breadcrumb(cat):
    # cat 不知道是几级分类
    breadcrumb = {
        'cat1':'',
        'cat2':'',
        'cat3':''
    }

    if cat.parent is None:
        # 分类没有父分类,肯定是一级分类
        breadcrumb['cat1']=cat
    elif cat.subs.count() == 0:
        #没有子类了,就是三级
        breadcrumb['cat3']=cat

        breadcrumb['cat2']=cat.parent

        breadcrumb['cat1']=cat.parent.parent
    else:
        breadcrumb['cat2']=cat
        breadcrumb['cat1']=cat.parent


    return breadcrumb

