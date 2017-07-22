from django.conf.urls import url, include

from post.views import PostListView, PostDetailView

urlpatterns = [
	url(r'^posts/$', PostListView.as_view(), name='post-list'),
	url(r'^posts/(?P<pk>[0-9]+)/$', PostDetailView.as_view(), name='post-detail'),
	url(r'^posts/(?P<pk>[0-9]+)/comments/', include('comment.urls')),
]
