from django.conf.urls import url
from . import views
urlpatterns = [
    # users:register
    url(r'^register/$',views.RegisterView.as_view(),name='register'),
    url(r'^usernames/(?P<username>[a-zA-Z0-9_]{5,20})/$',views.RegisterUsernameCountView.as_view(),name='usernamecount'),
    url(r'^login/$',views.LoginView.as_view(),name='login'),
    url(r'^logout/$',views.LogoutView.as_view(),name='logout'),
    url(r'^info/$',views.UserInfoView.as_view(),name='info'),
    url(r'^emails/$',views.EmailView.as_view(),name='email'),
    url(r'^emails/verification/$',views.EmailVerifyView.as_view(),name='emailverify'),
    url(r'^address/$',views.AddressView.as_view(),name='address'),
    url(r'^addresses/create/$',views.CreateAddressView.as_view(),name='createaddress'),
    url(r'^addresses/(?P<address_id>\d+)/$',views.UpdateDestoryAddressView.as_view(),name='updateaddress'),
    url(r'^browse_histories/$',views.HistoryView.as_view(),name='history'),
]