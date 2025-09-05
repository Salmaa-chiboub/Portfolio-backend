from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from cloudinary.models import CloudinaryField

from skills.models import Skill, SkillReference


def project_media_upload_to(instance, filename):
	# store under projects/<project_id>/<filename>
	return f"projects/{instance.project.id}/{filename}"


class Project(models.Model):
	title = models.CharField(max_length=200)
	description = models.TextField(blank=True)
	created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="projects")
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	# many-to-many relation to SkillReference via intermediate table ProjectSkillRef
	# we reference the global SkillReference catalog; per-owner Skill entries
	# are created automatically when a project references a SkillReference.
	skills = models.ManyToManyField(SkillReference, through="ProjectSkillRef", related_name="projects", blank=True)

	class Meta:
		ordering = ["-created_at"]

	def __str__(self):
		return self.title


class ProjectMedia(models.Model):
	project = models.ForeignKey(Project, related_name="media", on_delete=models.CASCADE)
	image = CloudinaryField('image')  # Utilisation de CloudinaryField pour le stockage Cloudinary
	order = models.PositiveSmallIntegerField(default=0)

	class Meta:
		ordering = ["order"]


class ProjectSkillRef(models.Model):
	project = models.ForeignKey(Project, on_delete=models.CASCADE)
	skill_reference = models.ForeignKey(SkillReference, on_delete=models.CASCADE)

	class Meta:
		unique_together = ("project", "skill_reference")

	def __str__(self):
		return f"{self.project} - {self.skill_reference.name}"


class ProjectLink(models.Model):
	project = models.ForeignKey(Project, related_name='links', on_delete=models.CASCADE)
	url = models.URLField()
	text = models.CharField(max_length=200)
	order = models.PositiveSmallIntegerField(default=0)

	class Meta:
		ordering = ['order']

	def __str__(self):
		return f"Link for {self.project.title}: {self.text}"
