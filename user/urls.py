from django.conf.urls import url

from user.views import SignupView, LoginView, LogoutView

urlpatterns = [
	url(r'^login/$', LoginView.as_view(), name='login'),
	url(r'^logout/$', LogoutView.as_view(), name='logout'),
	url(r'^signup/$', SignupView.as_view(), name='signup'),
]
