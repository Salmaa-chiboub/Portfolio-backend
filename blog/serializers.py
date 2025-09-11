import json
from django.db import transaction, IntegrityError
from rest_framework import serializers
from .models import Post, Image, Link


class ImageSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = Image
        fields = ('id', 'image', 'caption', 'post')
        read_only_fields = ('post',)

    def get_image(self, obj):
        """Return a Cloudinary URL only if it looks safe. Avoid returning malformed public IDs that would
        generate invalid Cloudinary URLs (e.g. containing spaces or apostrophes)."""
        try:
            if not obj.image:
                return None
            url = obj.image.url
            # if url contains encoded spaces or apostrophes, consider it invalid/unsafe
            if not url:
                return None
            if '%20' in url or '%27' in url or ' ' in url:
                return None
            return url
        except Exception:
            return None

    def delete(self, instance):
        # Delete the image from Cloudinary using the public_id
        try:
            public_id = None
            # CloudinaryField yields a CloudinaryResource with public_id attribute
            if hasattr(instance.image, 'public_id') and instance.image.public_id:
                public_id = instance.image.public_id
            # fall back: if image is a string URL, try to extract public_id from it (best-effort)
            if not public_id and isinstance(instance.image, str) and instance.image:
                # URL may contain /upload/<version>/<public_id>.<ext> - attempt simple extraction
                try:
                    parts = instance.image.split('/upload/')
                    if len(parts) > 1:
                        tail = parts[1]
                        # strip any transformations and extension
                        tail = tail.split('/')[-1]
                        public_id = tail.split('.')[0]
                except Exception:
                    public_id = None
            if public_id:
                try:
                    import cloudinary.uploader
                    cloudinary.uploader.destroy(public_id, invalidate=True)
                except Exception:
                    # ignore errors from Cloudinary delete
                    pass
        finally:
            # Delete the database record regardless
            instance.delete()
        return instance



class LinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = Link
        fields = ('id', 'url', 'text', 'order')
        read_only_fields = ('id',)


class PostSerializer(serializers.ModelSerializer):
    images = ImageSerializer(many=True, read_only=True)
    links = LinkSerializer(many=True, read_only=True)

    # Accept uploaded files
    uploaded_images = serializers.ListField(
        child=serializers.ImageField(allow_empty_file=False, use_url=False),
        write_only=True,
        required=False
    )

    # Accept JSON strings for metadata
    images_meta = serializers.CharField(write_only=True, required=False)
    # accept a JSON string via multipart/form-data; we will parse it manually in create/update
    links_data = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = Post
        fields = (
            'id', 'title', 'slug', 'content', 'created_at',
            'images', 'links', 'uploaded_images', 'images_meta', 'links_data'
        )
        read_only_fields = ('slug', 'created_at')

    def validate_title(self, value):
        """Ensure blog title is unique (case-insensitive). Return validation error with useful message."""
        title = (value or "").strip()
        if not title:
            raise serializers.ValidationError("Le titre est requis.")
        if len(title) > 200:
            raise serializers.ValidationError("Le titre ne peut pas dépasser 200 caractères.")
        qs = Post.objects.filter(title__iexact=title)
        # exclude current instance when updating
        instance = getattr(self, 'instance', None)
        if instance is not None:
            qs = qs.exclude(pk=instance.pk)
        if qs.exists():
            raise serializers.ValidationError("Un article avec ce titre existe déjà.")
        return title
        
    def validate_content(self, value):
        """Validate blog post content length."""
        if not value or not value.strip():
            raise serializers.ValidationError("Le contenu de l'article est requis.")
        if len(value) > 10000:
            raise serializers.ValidationError("Le contenu ne peut pas dépasser 10 000 caractères.")
        return value

    def update(self, instance, validated_data):
        uploaded_images = validated_data.pop('uploaded_images', None)
        images_meta = validated_data.pop('images_meta', None)
        links_data = validated_data.pop('links_data', None)

        # Update post fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        try:
            instance.save()
        except IntegrityError:
            raise serializers.ValidationError({"title": ["A blog post with this title already exists."]})

        # Handle image uploads if provided
        if uploaded_images is not None:
            try:
                images_meta = json.loads(images_meta) if isinstance(images_meta, str) else (images_meta or [])
            except (json.JSONDecodeError, TypeError):
                images_meta = []

            # Add new images without deleting existing ones. The frontend should perform explicit
            # DELETE requests for any existing images the user has removed, so we only need to
            # append newly uploaded files here.
            for i, image_file in enumerate(uploaded_images):
                caption = ''
                if i < len(images_meta) and isinstance(images_meta[i], dict) and 'caption' in images_meta[i]:
                    caption = images_meta[i]['caption']
                Image.objects.create(post=instance, image=image_file, caption=caption)

        # Handle links if provided
        if links_data is not None:
            # parse if string
            try:
                links_data = json.loads(links_data) if isinstance(links_data, str) else links_data
            except (json.JSONDecodeError, TypeError):
                links_data = []
            # Clear existing links
            instance.links.all().delete()
            # Add new links
            for link_data in links_data:
                # normalize
                if isinstance(link_data, str):
                    try:
                        ld = json.loads(link_data)
                    except Exception:
                        continue
                else:
                    ld = link_data
                if not isinstance(ld, dict):
                    continue
                url = ld.get('url')
                if not url or not isinstance(url, str) or not url.strip():
                    continue
                text = ld.get('text') or ''
                order = ld.get('order', 0)
                try:
                    order = int(order)
                except Exception:
                    order = 0
                Link.objects.create(post=instance, url=url.strip(), text=text.strip() if isinstance(text, str) else '', order=order)

        return instance

    def create(self, validated_data):
        uploaded_images = validated_data.pop('uploaded_images', [])
        images_meta = validated_data.pop('images_meta', '[]')
        links_data = validated_data.pop('links_data', '[]')

        try:
            images_meta = json.loads(images_meta) if isinstance(images_meta, str) else images_meta
        except (json.JSONDecodeError, TypeError):
            images_meta = []

        try:
            links_data = json.loads(links_data) if isinstance(links_data, str) else links_data
        except (json.JSONDecodeError, TypeError):
            links_data = []

        with transaction.atomic():
            try:
                post = Post.objects.create(**validated_data)
            except IntegrityError as e:
                # Convert DB uniqueness error into serializer validation error
                raise serializers.ValidationError({"title": ["A blog post with this title already exists."]})

            # Handle image uploads
            for i, image_file in enumerate(uploaded_images):
                caption = ''
                if i < len(images_meta) and 'caption' in images_meta[i]:
                    caption = images_meta[i]['caption']
                Image.objects.create(post=post, image=image_file, caption=caption)

            # Handle links
            for link_data in links_data:
                # normalize link_data
                if isinstance(link_data, str):
                    try:
                        ld = json.loads(link_data)
                    except Exception:
                        continue
                else:
                    ld = link_data
                if not isinstance(ld, dict):
                    continue
                url = ld.get('url')
                if not url or not isinstance(url, str) or not url.strip():
                    continue
                text = ld.get('text') or ''
                order = ld.get('order', 0)
                try:
                    order = int(order)
                except Exception:
                    order = 0
                Link.objects.create(post=post, url=url.strip(), text=text.strip() if isinstance(text, str) else '', order=order)

            return post
        return instance
