from rest_framework import serializers
from .models import HeroSection, About, ContactMessage


class HeroSectionSerializer(serializers.ModelSerializer):
    # Expose image URL for read, but allow image uploads via standard ImageField for write
    image = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model = HeroSection
        fields = ['id', 'headline', 'subheadline', 'image', 'instagram', 'linkedin', 'github', 'order', 'is_active']

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        if getattr(instance, 'image'):
            try:
                rep['image'] = instance.image.url
            except Exception:
                rep['image'] = None
        else:
            rep['image'] = None
        return rep


class AboutSerializer(serializers.ModelSerializer):
    class Meta:
        model = About
        fields = ['id', 'title', 'description', 'cv', 'hiring_email', 'updated_at']


class ContactMessageSerializer(serializers.ModelSerializer):
    def validate_name(self, value):
        if not value or len(value.strip()) < 2:
            raise serializers.ValidationError("Le nom est trop court.")
        return value.strip()

    def validate_email(self, value):
        if not value or "@" not in value:
            raise serializers.ValidationError("Email invalide.")
        return value.strip()

    def validate_subject(self, value):
        if value and len(value) > 200:
            raise serializers.ValidationError("Sujet trop long.")
        return value.strip() if value else value

    def validate_message(self, value):
        if not value or len(value.strip()) < 10:
            raise serializers.ValidationError("Message trop court.")
        return value.strip()

    class Meta:
        model = ContactMessage
        fields = ['id', 'name', 'email', 'subject', 'message', 'created_at', 'is_read']
        read_only_fields = ['created_at', 'is_read']
