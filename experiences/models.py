from django.db import models
from skills.models import SkillReference
from cloudinary.models import CloudinaryField

class Experience(models.Model):
    EXPERIENCE_TYPE_CHOICES = [
        ('job', 'Job'),
        ('internship', 'Internship'),
        ('freelance', 'Freelance'),
        ('project', 'Project'),
        ('volunteer', 'Volunteer'),
        ('other', 'Other'),
    ]

    title = models.CharField(max_length=200)           # Titre du poste ou projet
    company = models.CharField(max_length=200, blank=True, null=True)  # Nom de l’entreprise ou organisation
    location = models.CharField(max_length=200, blank=True, null=True)
    experience_type = models.CharField(
        max_length=20,
        choices=EXPERIENCE_TYPE_CHOICES,
        default='job'
    )
    start_date = models.DateField()
    end_date = models.DateField(blank=True, null=True)  # Peut être vide si encore en cours
    description = models.TextField(blank=True)         # Description des missions ou réalisations
    is_current = models.BooleanField(default=False)    # Si c’est l’expérience actuelle

    class Meta:
        ordering = ['-start_date']

    def __str__(self):
        return f"{self.title} @ {self.company or 'Indépendant'}"


class ExperienceSkillRef(models.Model):
	experience = models.ForeignKey(Experience, on_delete=models.CASCADE)
	skill_reference = models.ForeignKey(SkillReference, on_delete=models.CASCADE)

	class Meta:
		unique_together = ("experience", "skill_reference")

	def __str__(self):
		return f"{self.experience} - {self.skill_reference.name}"


class ExperienceLink(models.Model):
    experience = models.ForeignKey(Experience, related_name='links', on_delete=models.CASCADE)
    url = models.URLField()
    text = models.CharField(max_length=200)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.text} - {self.url}"
