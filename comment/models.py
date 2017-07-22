from django.db import models
from django.utils import timezone

from settings import settings
from utils.models import BlankModel
from post.models import Post


class Comment(BlankModel):
	post = models.ForeignKey('post.Post', related_name='comments', on_delete=models.CASCADE)
	user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='comment_user', null=True, on_delete=models.SET_NULL)
	desc = models.CharField(max_length=1000)
	created_on = models.DateTimeField()
	updated_on = models.DateTimeField()
	comment = models.ForeignKey('self', related_name='comment_on_comment', null=True, on_delete=models.CASCADE)
	approved_comment = models.BooleanField(default=True)

	def save(self, *args, **kwargs):
		if not self.id:
			self.created_on = timezone.now()
		self.updated_on = timezone.now()
		return super(Comment, self).save(*args, **kwargs)