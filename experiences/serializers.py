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
        child=serializers.IntegerField(), write_only=True, required=False
    )
    links = ExperienceLinkSerializer(many=True, read_only=True)
    links_data = serializers.ListField(
        child=serializers.DictField(), write_only=True, required=False
    )

    class Meta:
        model = Experience
        fields = "__all__"
        read_only_fields = ("id",)

    def create(self, validated_data):
        skills_data = validated_data.pop("skills_data", [])
        links_data = validated_data.pop("links_data", [])
        
        experience = Experience.objects.create(**validated_data)
        
        # Create skill references
        for skill_id in skills_data:
            ExperienceSkillRef.objects.create(experience=experience, skill_reference_id=skill_id)
            
        # Create links
        for link_data in links_data:
            ExperienceLink.objects.create(experience=experience, **link_data)
            
        return experience
        
    def update(self, instance, validated_data):
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
            for skill_id in skills_data:
                ExperienceSkillRef.objects.create(experience=instance, skill_reference_id=skill_id)
                
        # Update links if provided
        if links_data is not None:
            # Clear existing links
            instance.links.all().delete()
            # Add new links
            for link_data in links_data:
                ExperienceLink.objects.create(experience=instance, **link_data)
                
        return instance
