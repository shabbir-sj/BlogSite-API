from django.conf.urls import url

from comment.views import CommentListView, CommentDetailView

urlpatterns = [
	url(r'^$', CommentListView.as_view(), name='comment-list'),
	url(r'^(?P<pk>[0-9]+)/$', CommentDetailView.as_view(), name='comment-detail'),
]