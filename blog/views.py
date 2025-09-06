from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from .models import Post, Image, Link
from .serializers import PostSerializer, ImageSerializer, LinkSerializer
from core.permissions import IsSuperUser


class BlogPostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.prefetch_related("images", "links").all()
    serializer_class = PostSerializer
    lookup_field = 'slug'

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [permissions.AllowAny()]
        return [IsSuperUser()]

    @action(detail=False, methods=["delete"], permission_classes=[IsSuperUser])
    def delete_all(self, request):
        count, _ = Post.objects.all().delete()
        return Response(
            {"message": f"{count} posts deleted."},
            status=status.HTTP_204_NO_CONTENT
        )

    # Image management endpoints
    @action(detail=True, methods=['post'], permission_classes=[IsSuperUser])
    def add_images(self, request, slug=None):
        post = self.get_object()
        serializer = ImageSerializer(data=request.data, many=True)
        if serializer.is_valid():
            images = []
            for image_data in serializer.validated_data:
                image = Image.objects.create(
                    post=post,
                    image=image_data.get('image'),
                    caption=image_data.get('caption', '')
                )
                images.append(image)
            return Response(
                ImageSerializer(images, many=True).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['put', 'patch'], url_path=r'images/(?P<image_id>\\d+)', 
            permission_classes=[IsSuperUser])
    def update_image(self, request, slug=None, image_id=None):
        post = self.get_object()
        image = get_object_or_404(Image, id=image_id, post=post)
        serializer = ImageSerializer(image, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['delete'], url_path=r'images/(?P<image_id>\\d+)', permission_classes=[IsSuperUser])
    def delete_image(self, request, slug=None, image_id=None):
        post = self.get_object()
        image = get_object_or_404(Image, id=image_id, post=post)
        serializer = ImageSerializer()
        serializer.delete(image)
        return Response(
            {"message": "Image deleted successfully"},
            status=status.HTTP_204_NO_CONTENT
        )

    @action(detail=True, methods=['get'], url_path='images', permission_classes=[permissions.AllowAny])
    def list_images(self, request, slug=None):
        post = self.get_object()
        images = post.images.all()
        serializer = ImageSerializer(images, many=True)
        return Response(serializer.data)

    # Link management endpoints
    @action(detail=True, methods=['post'], permission_classes=[IsSuperUser])
    def add_links(self, request, slug=None):
        post = self.get_object()
        serializer = LinkSerializer(data=request.data, many=True)
        if serializer.is_valid():
            links = []
            for link_data in serializer.validated_data:
                link = Link.objects.create(post=post, **link_data)
                links.append(link)
            return Response(
                LinkSerializer(links, many=True).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['put', 'patch'], url_path=r'links/(?P<link_id>\\d+)', 
            permission_classes=[IsSuperUser])
    def update_link(self, request, slug=None, link_id=None):
        post = self.get_object()
        link = get_object_or_404(Link, id=link_id, post=post)
        serializer = LinkSerializer(link, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['delete'], url_path=r'links/(?P<link_id>\\d+)', permission_classes=[IsSuperUser])
    def delete_link(self, request, slug=None, link_id=None):
        post = self.get_object()
        link = get_object_or_404(Link, id=link_id, post=post)
        link.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['get'], url_path='links', permission_classes=[permissions.AllowAny])
    def list_links(self, request, slug=None):
        post = self.get_object()
        links = post.links.all().order_by('order')
        serializer = LinkSerializer(links, many=True)
        return Response(serializer.data)
