from rest_framework import viewsets, permissions, filters, status
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import get_object_or_404
from .models import Experience, ExperienceLink
from .serializers import ExperienceSerializer, ExperienceLinkSerializer
from rest_framework.decorators import action
from rest_framework.response import Response

class ExperiencePagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

class ExperienceViewSet(viewsets.ModelViewSet):
    queryset = Experience.objects.all()
    serializer_class = ExperienceSerializer
    pagination_class = ExperiencePagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend]
    search_fields = ["title", "company", "description"]
    ordering_fields = ["start_date", "end_date", "company"]
    filterset_fields = ["is_current", "company"]

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    @action(detail=False, methods=['delete'], permission_classes=[permissions.IsAuthenticated])
    def delete_all(self, request):
        count, _ = Experience.objects.all().delete()
        return Response(
            {"message": f"{count} experiences deleted."},
            status=status.HTTP_204_NO_CONTENT
        )
        
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def add_links(self, request, pk=None):
        experience = self.get_object()
        serializer = ExperienceLinkSerializer(data=request.data, many=True)
        if serializer.is_valid():
            links = []
            for link_data in serializer.validated_data:
                link = ExperienceLink.objects.create(
                    experience=experience,
                    **link_data
                )
                links.append(link)
            return Response(
                ExperienceLinkSerializer(links, many=True).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['put', 'patch'], url_path=r'links/(?P<link_id>\\d+)',
            permission_classes=[permissions.IsAuthenticated])
    def update_link(self, request, pk=None, link_id=None):
        experience = self.get_object()
        link = get_object_or_404(ExperienceLink, id=link_id, experience=experience)
        serializer = ExperienceLinkSerializer(link, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['delete'], url_path=r'links/(?P<link_id>\\d+)', 
            permission_classes=[permissions.IsAuthenticated])
    def delete_link(self, request, pk=None, link_id=None):
        experience = self.get_object()
        link = get_object_or_404(ExperienceLink, id=link_id, experience=experience)
        link.delete()
        return Response(
            {"message": "Link deleted successfully"},
            status=status.HTTP_204_NO_CONTENT
        )
    
    @action(detail=True, methods=['get'], url_path='links', 
            permission_classes=[permissions.AllowAny])
    def list_links(self, request, pk=None):
        experience = self.get_object()
        links = experience.links.all().order_by('order')
        serializer = ExperienceLinkSerializer(links, many=True)
        return Response(serializer.data)
