from rest_framework import serializers

from .models import Skill, SkillReference


class SkillReferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = SkillReference
        fields = ("id", "name", "icon")
        read_only_fields = ("id",)


class SkillSerializer(serializers.ModelSerializer):
    reference = SkillReferenceSerializer(read_only=True)
    reference_id = serializers.PrimaryKeyRelatedField(
        queryset=SkillReference.objects.all(),
        source="reference",
        write_only=True
    )

    class Meta:
        model = Skill
        fields = ("id", "reference_id", "reference")
        read_only_fields = ("id",)

    def validate(self, attrs):
        reference = attrs.get("reference")

        # Vérifier si ce skill existe déjà
        if Skill.objects.filter(reference=reference).exists():
            raise serializers.ValidationError(
                {"reference_id": "Ce skill existe déjà dans le portfolio."}
            )

        return attrs
