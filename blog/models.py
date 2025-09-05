from django.db import models
from django.utils.text import slugify
from cloudinary.models import CloudinaryField


class Post(models.Model):
    title = models.CharField(max_length=200, unique=True)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)


class Image(models.Model):
    post = models.ForeignKey(Post, related_name='images', on_delete=models.CASCADE)
    image = CloudinaryField('image')  # Remplacement par CloudinaryField
    caption = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return f"Image for {self.post.title}"


class Link(models.Model):
    post = models.ForeignKey(Post, related_name='links', on_delete=models.CASCADE)
    url = models.URLField()
    text = models.CharField(max_length=200)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"Link for {self.post.title}: {self.text}"
