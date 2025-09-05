import json
from io import BytesIO
from PIL import Image as PILImage
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse

from .models import Post, Image

User = get_user_model()


class BlogPostViewSetTests(APITestCase):
    def setUp(self):
        # Create a regular user
        self.user = User.objects.create_user(username='testuser', password='password123')

        # Create a superuser
        self.superuser = User.objects.create_superuser(username='admin', password='password123')

        # Create some posts
        self.post1 = Post.objects.create(
            title='First Post',
            content='This is the first post.',
        )
        self.post2 = Post.objects.create(
            title='Second Post',
            content='This is the second post.',
        )

    def test_list_posts_anonymous(self):
        """Ensure anonymous users can see all posts."""
        url = reverse('post-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)


    def test_retrieve_post_anonymous(self):
        """Ensure anonymous users can retrieve any post."""
        url = reverse('post-detail', kwargs={'slug': self.post1.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], self.post1.title)


    def test_create_post_superuser(self):
        """Ensure superuser can create a post with nested images and links."""
        self.client.force_authenticate(user=self.superuser)
        url = reverse('post-list')

        # Create a dummy image file in memory
        img_io = BytesIO()
        image = PILImage.new('RGB', (100, 100), 'red')
        image.save(img_io, 'jpeg')
        img_io.seek(0)
        dummy_image = SimpleUploadedFile(
            "test_image.jpg",
            img_io.read(),
            content_type="image/jpeg"
        )

        data = {
            'title': 'New Post by Admin',
            'content': 'Content here.',
            'uploaded_images': [dummy_image],
            'images_meta': json.dumps([{'caption': 'A nice image'}]),
            'links_data': json.dumps([{'url': 'http://example.com', 'text': 'Example Site'}])
        }

        response = self.client.post(url, data, format='multipart')
        self.assertEqual(
            response.status_code, status.HTTP_201_CREATED,
            f"Failed to create post. Errors: {response.data}"
        )
        self.assertEqual(Post.objects.count(), 3)
        new_post = Post.objects.get(title='New Post by Admin')
        self.assertEqual(new_post.images.count(), 1)
        self.assertEqual(new_post.links.count(), 1)
        self.assertEqual(new_post.images.first().caption, 'A nice image')

        # Verify the new post is visible to anonymous users
        self.client.logout()
        list_url = reverse('post-list')
        response = self.client.get(list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3) # The two original posts + the new one
        self.assertIn('New Post by Admin', [p['title'] for p in response.data])

    def test_create_post_regular_user_fails(self):
        """Ensure regular users cannot create posts."""
        self.client.force_authenticate(user=self.user)
        url = reverse('post-list')
        data = {'title': 'New Post by User', 'content': 'Content.'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


    def test_delete_post_superuser(self):
        """Ensure superuser can delete a post."""
        self.client.force_authenticate(user=self.superuser)
        url = reverse('post-detail', kwargs={'slug': self.post1.slug})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Post.objects.count(), 1)

    def test_update_post_superuser(self):
        """Ensure superuser can update a post."""
        self.client.force_authenticate(user=self.superuser)
        url = reverse('post-detail', kwargs={'slug': self.post1.slug})
        data = {'title': 'Updated Title', 'content': 'Updated content.'}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.post1.refresh_from_db()
        self.assertEqual(self.post1.title, 'Updated Title')

