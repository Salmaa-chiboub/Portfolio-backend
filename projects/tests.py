from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from django.core.files.uploadedfile import SimpleUploadedFile
from .models import Project, ProjectMedia
import base64


# minimal 1x1 jpeg
_SAMPLE_JPEG = base64.b64decode(
	'/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAP//////////////////////////////////////////////////////////////////////////////////////2wBDAf//////////////////////////////////////////////////////////////////////////////////////wAARCAABAAEDASIAAhEBAxEB/8QAFwABAQEBAAAAAAAAAAAAAAAAAAECA//EABUBAQEAAAAAAAAAAAAAAAAAAAAB/8QAFgEBAQEAAAAAAAAAAAAAAAAAAAEH/8QAFBEBAAAAAAAAAAAAAAAAAAAAAP/aAAwDAQACEQMRAD8A/9k='
)


class ProjectsAPITest(APITestCase):
	def setUp(self):
		User = get_user_model()
		self.user = User.objects.create_user(username='tester', password='pass')
		self.client = APIClient()
		# create a sample project owned by user
		self.project = Project.objects.create(title='My Project', description='Desc', created_by=self.user)

	def test_list_projects_public(self):
		url = reverse('project-list')
		resp = self.client.get(url)
		self.assertEqual(resp.status_code, status.HTTP_200_OK)

	def test_retrieve_project(self):
		url = reverse('project-detail', args=[self.project.id])
		resp = self.client.get(url)
		self.assertEqual(resp.status_code, status.HTTP_200_OK)
		self.assertEqual(resp.data['title'], self.project.title)

	def test_create_project_requires_auth(self):
		url = reverse('project-list')
		data = {'title': 'New', 'description': 'x'}
		resp = self.client.post(url, data, format='json')
		self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

	def test_create_project_with_images(self):
		self.client.force_authenticate(user=self.user)
		url = reverse('project-list')
		img1 = SimpleUploadedFile('a.jpg', _SAMPLE_JPEG, content_type='image/jpeg')
		img2 = SimpleUploadedFile('b.jpg', _SAMPLE_JPEG, content_type='image/jpeg')
		data = {'title': 'WithImgs', 'description': 'd', 'media_files': [img1, img2]}
		resp = self.client.post(url, data, format='multipart')
		self.assertIn(resp.status_code, (status.HTTP_201_CREATED, status.HTTP_200_OK))
		pid = resp.data.get('id')
		project = Project.objects.get(id=pid)
		self.assertEqual(project.media.count(), 2)

	def test_create_project_more_than_three_images_fails(self):
		self.client.force_authenticate(user=self.user)
		url = reverse('project-list')
		imgs = [SimpleUploadedFile(f'{i}.jpg', _SAMPLE_JPEG, content_type='image/jpeg') for i in range(4)]
		data = {'title': 'TooMany', 'description': 'd', 'media_files': imgs}
		resp = self.client.post(url, data, format='multipart')
		self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

	def test_update_replace_media(self):
		self.client.force_authenticate(user=self.user)
		# add existing media
		ProjectMedia.objects.create(project=self.project, image=SimpleUploadedFile('o.jpg', _SAMPLE_JPEG, content_type='image/jpeg'), order=0)
		url = reverse('project-detail', args=[self.project.id])
		newimg = SimpleUploadedFile('n.jpg', _SAMPLE_JPEG, content_type='image/jpeg')
		data = {'media_files': [newimg]}
		resp = self.client.patch(url, data, format='multipart')
		self.assertIn(resp.status_code, (status.HTTP_200_OK, status.HTTP_202_ACCEPTED))
		self.project.refresh_from_db()
		self.assertEqual(self.project.media.count(), 1)

	def test_delete_project(self):
		self.client.force_authenticate(user=self.user)
		url = reverse('project-detail', args=[self.project.id])
		resp = self.client.delete(url)
		self.assertIn(resp.status_code, (status.HTTP_204_NO_CONTENT, status.HTTP_200_OK))
