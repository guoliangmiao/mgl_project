from django.conf.urls import url
from apps.goods import views

urlpatterns = [

    url(r'^list/(?P<category_id>\d+)/(?P<page_num>\d+)/$',views.ListView.as_view(),name='list'),
    url(r'^hot/(?P<category_id>\d+)/$',views.HotView.as_view(),name='hot'),
    url(r'^detail/(?P<sku_id>\d+)/$',views.DetailView.as_view(),name='detail'),
    url(r'^detail/visit/(?P<category_id>\d+)/$',views.CategoryVisitView.as_view(),name='visit'),
]