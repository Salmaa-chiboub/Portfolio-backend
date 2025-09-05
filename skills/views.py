from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticated, AllowAny

from .models import Skill, SkillReference
from .serializers import SkillSerializer, SkillReferenceSerializer


class SkillReferenceViewSet(viewsets.ReadOnlyModelViewSet):
	"""Read-only endpoint for the canonical skill catalog.

	Supports searching by name via DRF SearchFilter: ?search=python
	"""
	queryset = SkillReference.objects.all()
	serializer_class = SkillReferenceSerializer
	filter_backends = [filters.SearchFilter]
	search_fields = ["name"]


class SkillViewSet(viewsets.ModelViewSet):
	"""Full CRUD for Skill entries attached to the portfolio."""
	queryset = Skill.objects.select_related("reference").all()
	serializer_class = SkillSerializer

	def get_permissions(self):
		if self.action in ["list", "retrieve"]:
			return [AllowAny()]
		return [IsAuthenticated()]
