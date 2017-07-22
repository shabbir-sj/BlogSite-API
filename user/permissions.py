from rest_framework.permissions import IsAuthenticated


class IsAdmin(IsAuthenticated):
	"""
	permission class to set Admin permission.
	"""
	def has_permission(self, request, view):
		if super().has_permission(request, view):
			return request.user.is_superuser


class IsAuthor(IsAuthenticated):
	"""
	permission class to set author permission.
	"""
	def has_permission(self, request, view):
		return super().has_permission(request, view)
