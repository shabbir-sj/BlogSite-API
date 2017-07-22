from django.db import models
from django.utils import timezone

from utils.models import BlankModel
from django.conf import settings


# Create your models here.

class Post(BlankModel):
	user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='post_user', null=True, on_delete=models.SET_NULL)
	title = models.CharField(max_length=500)
	desc = models.CharField(max_length=10000)
	created_on = models.DateTimeField()
	updated_on = models.DateTimeField()

	def save(self, *args, **kwargs):
		if not self.id:
			self.created_on = timezone.now()
		self.updated_on = timezone.now()
		return super(Post, self).save(*args, **kwargs)
