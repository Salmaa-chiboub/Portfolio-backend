from rest_framework import serializers
from .models import Experience, ExperienceSkillRef, ExperienceLink

class ExperienceSkillRefSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source="skill_reference.name", read_only=True)
    icon = serializers.URLField(source="skill_reference.icon", read_only=True)
    class Meta:
        model = ExperienceSkillRef
        fields = ("id", "experience", "skill_reference", "name", "icon")
        read_only_fields = ("id",)

class ExperienceLinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExperienceLink
        fields = ('id', 'url', 'text', 'order')
        read_only_fields = ('id',)


class ExperienceSerializer(serializers.ModelSerializer):
    skills = ExperienceSkillRefSerializer(source="experienceskillref_set", many=True, read_only=True)
    skills_data = serializers.ListField(
        child=serializers.CharField(), write_only=True, required=False
    )
    links = ExperienceLinkSerializer(many=True, read_only=True)
    links_data = serializers.ListField(
        child=serializers.DictField(), write_only=True, required=False
    )

    class Meta:
        model = Experience
        fields = "__all__"
        read_only_fields = ("id",)

    def validate_skills_data(self, value):
        """
        Handle skills sent as:
        - List of integers: [1, 2, 3] (existing skill IDs)
        - List of strings: ["React", "Python"] (new skill names)
        - Mixed list: [1, "New Skill"]
        """
        from skills.models import SkillReference
        
        if not isinstance(value, (list, tuple)):
            if isinstance(value, str):
                try:
                    value = json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    value = [s.strip() for s in value.split(',') if s.strip()]
            else:
                value = [value]

        skill_data = []
        for item in value:
            if isinstance(item, (int, str)) and str(item).isdigit():
                skill_data.append({'type': 'id', 'value': int(item)})
            elif isinstance(item, str):
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
        
    def create(self, validated_data):
        from skills.models import SkillReference
        
        skills_data = validated_data.pop("skills_data", [])
        links_data = validated_data.pop("links_data", [])
        
        with transaction.atomic():
            experience = Experience.objects.create(**validated_data)
            
            # Create skill references
            for skill_item in skills_data:
                if skill_item['type'] == 'id':
                    # Existing skill reference
                    ExperienceSkillRef.objects.create(
                        experience=experience, 
                        skill_reference_id=skill_item['value']
                    )
                else:
                    # New skill - create SkillReference first
                    skill_ref = SkillReference.objects.create(
                        name=skill_item['value'],
                        icon=''  # You might want to handle this differently
                    )
                    ExperienceSkillRef.objects.create(
                        experience=experience,
                        skill_reference=skill_ref
                    )
            
            # Create links
            for link_data in links_data:
                ExperienceLink.objects.create(experience=experience, **link_data)
                
            return experience
        
    def update(self, instance, validated_data):
        from skills.models import SkillReference
        
        skills_data = validated_data.pop("skills_data", None)
        links_data = validated_data.pop("links_data", None)
        
        # Update experience fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update skills if provided
        if skills_data is not None:
            # Clear existing skills
            instance.experienceskillref_set.all().delete()
            
            # Add new skills
            for skill_item in skills_data:
                if skill_item['type'] == 'id':
                    # Existing skill reference
                    ExperienceSkillRef.objects.create(
                        experience=instance,
                        skill_reference_id=skill_item['value']
                    )
                else:
                    # New skill - create SkillReference first
                    skill_ref = SkillReference.objects.create(
                        name=skill_item['value'],
                        icon=''  # You might want to handle this differently
                    )
                    ExperienceSkillRef.objects.create(
                        experience=instance,
                        skill_reference=skill_ref
                    )
                
        # Update links if provided
        if links_data is not None:
            # Clear existing links
            instance.links.all().delete()
            # Add new links
            for link_data in links_data:
                ExperienceLink.objects.create(experience=instance, **link_data)
                
        return instance
