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
    # Handle skills sent as multiple fields with the same name
    skills = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False
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
        if len(value) > 10000:
            raise serializers.ValidationError("La description ne peut pas dépasser 10 000 caractères.")
        return value


    def validate_skills(self, value):
        """
        Handle skills sent as:
        - List of integers: [1, 2, 3] (existing skill IDs)
        - List of strings: ["React", "Python"] (new skill names)
        - Mixed list: [1, "New Skill"]
        - Comma-separated string: "1,2,3" or "React,Python"
        - Multiple fields with same name: skills=1&skills=React
        """
        from skills.models import SkillReference
        
        # If it's already a list, use it as is
        if not isinstance(value, (list, tuple)):
            # If it's a string, try to parse as JSON or comma-separated
            if isinstance(value, str):
                try:
                    value = json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    value = [s.strip() for s in value.split(',') if s.strip()]
            # If it's a single value, convert to list
            else:
                value = [value]

        # Process each skill (could be ID or name)
        skill_data = []
        for item in value:
            if isinstance(item, (int, str)) and str(item).isdigit():
                # It's a skill ID
                skill_data.append({'type': 'id', 'value': int(item)})
            elif isinstance(item, str):
                # It's a new skill name
                if not item.strip():
                    continue
                skill_data.append({'type': 'name', 'value': item.strip()})
            else:
                raise serializers.ValidationError(f"Invalid skill format: {item}")

        # Check for duplicate skill names (case-insensitive)
        skill_names = [s['value'].lower() for s in skill_data if s['type'] == 'name']
        if len(skill_names) != len(set(skill_names)):
            raise serializers.ValidationError("Duplicate skill names are not allowed")

        # Check if all skill IDs exist
        skill_ids = [s['value'] for s in skill_data if s['type'] == 'id']
        if skill_ids:
            existing_skills = set(SkillReference.objects.filter(
                id__in=skill_ids
            ).values_list('id', flat=True))
            
            missing_skills = [sid for sid in skill_ids if sid not in existing_skills]
            if missing_skills:
                raise serializers.ValidationError(
                    f"The following skill IDs do not exist: {', '.join(map(str, missing_skills))}"
                )
            
        return skill_data

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
        from skills.models import SkillReference
        
        media_files = validated_data.pop("media_files", [])
        skills_data = validated_data.pop("skills", [])
        links_data = validated_data.pop("links_data", [])
        
        with transaction.atomic():
            project = Project.objects.create(**validated_data)
            
            # Handle media files
            for media_file in media_files:
                ProjectMedia.objects.create(project=project, image=media_file)
            
            # Handle skills
            for skill_item in skills_data:
                if skill_item['type'] == 'id':
                    # Existing skill reference
                    ProjectSkillRef.objects.create(
                        project=project, 
                        skill_reference_id=skill_item['value']
                    )
                else:
                    # New skill - create SkillReference first
                    skill_ref = SkillReference.objects.create(
                        name=skill_item['value'],
                        icon=''  # You might want to handle this differently
                    )
                    ProjectSkillRef.objects.create(
                        project=project,
                        skill_reference=skill_ref
                    )
            
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
            from skills.models import SkillReference
            
            # Clear existing skills
            instance.skills.clear()
            
            # Add new skills
            for skill_item in skills_data:
                if skill_item['type'] == 'id':
                    # Existing skill reference
                    ProjectSkillRef.objects.create(
                        project=instance,
                        skill_reference_id=skill_item['value']
                    )
                else:
                    # New skill - create SkillReference first
                    skill_ref = SkillReference.objects.create(
                        name=skill_item['value'],
                        icon=''  # You might want to handle this differently
                    )
                    ProjectSkillRef.objects.create(
                        project=instance,
                        skill_reference=skill_ref
                    )
        
        # Handle links if provided
        if links_data is not None:
            # Clear existing links
            instance.links.all().delete()
            # Add new links
            for link_data in links_data:
                ProjectLink.objects.create(project=instance, **link_data)
                
        return instance
