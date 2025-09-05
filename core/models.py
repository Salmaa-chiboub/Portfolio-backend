from django.db import models
from django.utils import timezone
from cloudinary.models import CloudinaryField
from cloudinary_storage.storage import RawMediaCloudinaryStorage


class HeroSection(models.Model):
	headline = models.CharField(max_length=200)
	subheadline = models.CharField(max_length=400, blank=True)
	image = CloudinaryField('image', blank=True, null=True)  # Remplacement par CloudinaryField
	instagram = models.URLField(blank=True)
	linkedin = models.URLField(blank=True)
	github = models.URLField(blank=True)
	order = models.PositiveIntegerField(default=0)
	is_active = models.BooleanField(default=True)

	class Meta:
		ordering = ['order']

	def __str__(self):
		return self.headline

	def clean(self):
		# Ensure only one HeroSection instance can be created
		if not self.pk and HeroSection.objects.exists():
			from django.core.exceptions import ValidationError
			raise ValidationError('Only one HeroSection instance is allowed.')

	def save(self, *args, **kwargs):
		self.full_clean()
		return super().save(*args, **kwargs)


class About(models.Model):
	title = models.CharField(max_length=200, default='About')
	description = models.TextField(blank=True)
	cv = models.FileField(storage=RawMediaCloudinaryStorage(), blank=True, null=True)  # Suppression de l'argument incorrect
	hiring_email = models.EmailField(blank=True, null=True)
	updated_at = models.DateTimeField(auto_now=True)

	def __str__(self):
		return self.title

	def clean(self):
		# Ensure only one About instance can be created
		if not self.pk and About.objects.exists():
			from django.core.exceptions import ValidationError
			raise ValidationError('Only one About instance is allowed.')

	def save(self, *args, **kwargs):
		self.full_clean()
		return super().save(*args, **kwargs)


class ContactMessage(models.Model):
	name = models.CharField(max_length=200, blank=True)
	email = models.EmailField()
	subject = models.CharField(max_length=200, blank=True)
	message = models.TextField()
	created_at = models.DateTimeField(default=timezone.now)
	is_read = models.BooleanField(default=False)

	def __str__(self):
		return f"{self.email} - {self.subject or 'no-subject'}"
