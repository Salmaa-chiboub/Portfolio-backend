from rest_framework import viewsets, status, filters, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend
from .models import Project, ProjectMedia, ProjectSkillRef, ProjectLink
from .serializers import ProjectSerializer, ProjectMediaSerializer, ProjectLinkSerializer
from .filters import ProjectFilter
from skills.models import SkillReference
from core.permissions import IsSuperUser
from django.shortcuts import get_object_or_404
import cloudinary.uploader


class IsAuthenticatedForWrite(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_authenticated


class ProjectViewSet(viewsets.ModelViewSet):
    # skills is a ManyToMany to SkillReference, so prefetch the skills relation directly
    queryset = Project.objects.all().prefetch_related('skills', 'media')
    serializer_class = ProjectSerializer
    permission_classes = (IsAuthenticatedForWrite,)
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = ['title', 'description']
    filterset_class = ProjectFilter

    def get_queryset(self):
        qs = super().get_queryset()
        skill = self.request.query_params.get('skill')
        if skill:
            qs = qs.filter(skills__reference__name__iexact=skill)
        return qs

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def add_media(self, request, pk=None):
        project = self.get_object()
        serializer = ProjectMediaSerializer(data=request.data, many=True)
        if serializer.is_valid():
            media_items = []
            for media_data in serializer.validated_data:
                media = ProjectMedia.objects.create(
                    project=project,
                    image=media_data.get('image'),
                    order=media_data.get('order', 0)
                )
                media_items.append(media)
            return Response(
                ProjectMediaSerializer(media_items, many=True).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['put', 'patch'], url_path=r'media/(?P<media_id>\\d+)',
            permission_classes=[permissions.IsAuthenticated])
    def update_media(self, request, pk=None, media_id=None):
        project = self.get_object()
        media = get_object_or_404(ProjectMedia, id=media_id, project=project)
        serializer = ProjectMediaSerializer(media, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['delete'], url_path=r'media/(?P<media_id>\\d+)', 
            permission_classes=[permissions.IsAuthenticated])
    def delete_media(self, request, pk=None, media_id=None):
        project = self.get_object()
        media = get_object_or_404(ProjectMedia, id=media_id, project=project)
        serializer = ProjectMediaSerializer()
        serializer.delete(media)
        return Response(
            {"message": "Media deleted successfully"},
            status=status.HTTP_204_NO_CONTENT
        )

    @action(detail=True, methods=['get'], url_path='media', 
            permission_classes=[permissions.AllowAny])
    def list_media(self, request, pk=None):
        project = self.get_object()
        media = project.media.all().order_by('order')
        serializer = ProjectMediaSerializer(media, many=True)
        return Response(serializer.data)
    
    # Link management endpoints
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def add_links(self, request, pk=None):
        project = self.get_object()
        serializer = ProjectLinkSerializer(data=request.data, many=True)
        if serializer.is_valid():
            links = []
            for link_data in serializer.validated_data:
                link = ProjectLink.objects.create(project=project, **link_data)
                links.append(link)
            return Response(
                ProjectLinkSerializer(links, many=True).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['put', 'patch'], url_path=r'links/(?P<link_id>\\d+)',
            permission_classes=[permissions.IsAuthenticated])
    def update_link(self, request, pk=None, link_id=None):
        project = self.get_object()
        link = get_object_or_404(ProjectLink, id=link_id, project=project)
        serializer = ProjectLinkSerializer(link, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['delete'], url_path=r'links/(?P<link_id>\\d+)', 
            permission_classes=[permissions.IsAuthenticated])
    def delete_link(self, request, pk=None, link_id=None):
        project = self.get_object()
        link = get_object_or_404(ProjectLink, id=link_id, project=project)
        link.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['get'], url_path='links', 
            permission_classes=[permissions.AllowAny])
    def list_links(self, request, pk=None):
        project = self.get_object()
        links = project.links.all().order_by('order')
        serializer = ProjectLinkSerializer(links, many=True)
        return Response(serializer.data)
