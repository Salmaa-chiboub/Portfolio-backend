from rest_framework import serializers
from .models import Project, ProjectMedia, ProjectSkillRef,ProjectLink
from skills.models import Skill, SkillReference
from django.db import transaction
import cloudinary.uploader
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError as DjangoValidationError
from .models import Project, ProjectMedia, ProjectSkillRef
import json

class ProjectMediaSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = ProjectMedia
        fields = ("id", "image", "order", "project")
        read_only_fields = ("project",)

    def get_image(self, obj):
        """Return a Cloudinary URL only if it looks safe. Avoid returning malformed public IDs that would
        generate invalid Cloudinary URLs (e.g. containing spaces or apostrophes)."""
        try:
            if not obj.image:
                return None
            url = obj.image.url
            if not url:
                return None
            if '%20' in url or '%27' in url or ' ' in url:
                return None
            return url
        except Exception:
            return None
        
    def delete(self, instance):
        # Delete the image from Cloudinary using public_id when available
        try:
            public_id = None
            if hasattr(instance.image, 'public_id') and instance.image.public_id:
                public_id = instance.image.public_id
            if not public_id and isinstance(instance.image, str) and instance.image:
                try:
                    parts = instance.image.split('/upload/')
                    if len(parts) > 1:
                        tail = parts[1]
                        tail = tail.split('/')[-1]
                        public_id = tail.split('.')[0]
                except Exception:
                    public_id = None
            if public_id:
                try:
                    import cloudinary.uploader
                    cloudinary.uploader.destroy(public_id, invalidate=True)
                except Exception:
                    pass
        finally:
            instance.delete()
        return instance

class ProjectSkillRefSerializer(serializers.ModelSerializer):
    # On renvoie seulement les infos utiles de SkillReference
    name = serializers.CharField(source="skill_reference.name", read_only=True)
    icon = serializers.CharField(source="skill_reference.icon", read_only=True)

    class Meta:
        model = ProjectSkillRef
        fields = ("id", "name", "icon")
        read_only_fields = ("id", "name", "icon")



class ProjectLinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectLink
        fields = ('id', 'url', 'text', 'order')
        read_only_fields = ('id',)


class ProjectSerializer(serializers.ModelSerializer):
    media = ProjectMediaSerializer(many=True, read_only=True)
    links = ProjectLinkSerializer(many=True, read_only=True)
    media_files = serializers.ListField(
        child=serializers.ImageField(), write_only=True, required=False
    )
    # skills envoyés comme IDs en écriture
    skills = serializers.ListField(
        child=serializers.IntegerField(), write_only=True, required=False
    )
    # skills affichés en lecture avec nom + icon
    skills_list = ProjectSkillRefSerializer(source="projectskillref_set", many=True, read_only=True)
    # links data for creation/update (accepts JSON string via multipart/form-data)
    links_data = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = Project
        fields = (
            "id",
            "title",
            "description",
            "created_by",
            "created_at",
            "updated_at",
            "media",
            "media_files",
            "skills",       # input (IDs)
            "skills_list",  # output (IDs + name + icon)
            "links",        # output (liens en lecture)
            "links_data",   # input (liens en écriture)
        )
        read_only_fields = ("created_by", "created_at", "updated_at")


    def validate_title(self, value):
        if not value.strip():
            raise serializers.ValidationError("Title cannot be empty.")
        if len(value) > 200:
            raise serializers.ValidationError("Title cannot exceed 200 characters.")
        return value

    def validate_description(self, value):
        if len(value) > 2000:
            raise serializers.ValidationError("Description cannot exceed 2000 characters.")
        return value


    def validate_skills(self, value):
        """
        Vérifie que chaque ID existe et supprime les doublons.
        Accepts JSON string (from multipart/form-data) or list/tuple.
        """
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
            except Exception:
                # also accept comma separated
                parsed = [s.strip() for s in value.split(',') if s.strip()]
            value = parsed

        if not isinstance(value, (list, tuple)):
            raise serializers.ValidationError("Skills must be a list of IDs.")

        if len(value) > 20:
            raise serializers.ValidationError("You can attach at most 20 skills per project.")

        unique_ids = set()
        missing = []
        for skill_id in value:
            try:
                sid = int(skill_id)
            except Exception:
                raise serializers.ValidationError(f"Invalid skill id: {skill_id}")
            if sid in unique_ids:
                continue
            unique_ids.add(sid)
            if not SkillReference.objects.filter(id=sid).exists():
                missing.append(sid)

        if missing:
            raise serializers.ValidationError(
                f"SkillReference IDs not found: {', '.join(map(str, missing))}"
            )
        return list(unique_ids)

    def validate_media_files(self, value):
        """
        Max 5 fichiers, taille et format validés.
        """
        if len(value) > 5:
            raise serializers.ValidationError("You can upload at most 5 images per project.")

        allowed_types = {"image/jpeg", "image/png", "image/webp"}
        max_size = 5 * 1024 * 1024  # 5MB

        for f in value:
            if hasattr(f, "content_type") and f.content_type not in allowed_types:
                raise serializers.ValidationError(
                    f"Unsupported file type {f.content_type}. Allowed: JPEG, PNG, WEBP."
                )
            if hasattr(f, "size") and f.size > max_size:
                raise serializers.ValidationError(
                    f"File {f.name} is too large ({f.size/1024:.1f} KB). Max 5MB."
                )
        return value

    def validate_links_data(self, value):
        """
        Accept either a list of link dicts, or a JSON string when sent via multipart/form-data.
        Each link must at least include a url; text and order are optional.
        """
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
            except Exception:
                raise serializers.ValidationError("links_data must be a JSON array of objects")
            value = parsed

        if not isinstance(value, list):
            raise serializers.ValidationError("links_data must be a list of objects")

        cleaned = []
        for i, item in enumerate(value):
            if not isinstance(item, dict):
                raise serializers.ValidationError(f"links_data[{i}] must be an object")
            url = item.get("url")
            if not url or not isinstance(url, str) or not url.strip():
                raise serializers.ValidationError(f"links_data[{i}].url is required")
            text = item.get("text") or ""
            order = item.get("order", i)
            cleaned.append({"url": url.strip(), "text": text.strip() if isinstance(text, str) else "", "order": int(order)})
        return cleaned


    def get_skills_list(self, obj):
        return [sr.name for sr in obj.skills.all()]

    def create(self, validated_data):
        media_files = validated_data.pop("media_files", [])
        skills_data = validated_data.pop("skills", [])
        links_data = validated_data.pop("links_data", [])
        
        with transaction.atomic():
            project = Project.objects.create(**validated_data)
            
            # Handle media files
            for media_file in media_files:
                ProjectMedia.objects.create(project=project, image=media_file)
                
            # Handle skills
            for skill_id in skills_data:
                ProjectSkillRef.objects.create(project=project, skill_reference_id=skill_id)
            
            # Handle links
            for link_data in links_data:
                ProjectLink.objects.create(project=project, **link_data)
                
            return project

    def update(self, instance, validated_data):
        media_files = validated_data.pop("media_files", None)
        skills_data = validated_data.pop("skills", None)
        links_data = validated_data.pop("links_data", None)
        
        # Update project fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Handle media files if provided
        if media_files is not None:
            # Add new media without deleting existing ones. The frontend is expected to
            # call DELETE on any media the user removed prior to submitting the form.
            for media_file in media_files:
                ProjectMedia.objects.create(project=instance, image=media_file)
        
        # Handle skills if provided
        if skills_data is not None:
            # Clear existing skills
            instance.skills.clear()
            # Add new skills
            for skill_id in skills_data:
                ProjectSkillRef.objects.create(project=instance, skill_reference_id=skill_id)
        
        # Handle links if provided
        if links_data is not None:
            # Clear existing links
            instance.links.all().delete()
            # Add new links
            for link_data in links_data:
                ProjectLink.objects.create(project=instance, **link_data)
                
        return instance
