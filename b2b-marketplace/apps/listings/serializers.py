from rest_framework import serializers
from .models import Category, Material, Design, TechPack, Certification, Tag
from apps.accounts.serializers import UserSerializer # For seller/designer info
from django.conf import settings
from django.contrib.auth import get_user_model # ADD THIS

User = get_user_model()

class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'name', 'slug']

class CategorySerializer(serializers.ModelSerializer):
    subcategories_count = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'description', 'parent_category', 'subcategories_count']
        read_only_fields = ['slug']

    def get_subcategories_count(self, obj):
        return obj.subcategories.count()

class CertificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Certification
        fields = '__all__'

class TechPackSerializer(serializers.ModelSerializer):
    class Meta:
        model = TechPack
        fields = ['id', 'design', 'file', 'version', 'notes', 'uploaded_at']
        read_only_fields = ['uploaded_at']

class MaterialSerializer(serializers.ModelSerializer):
    seller = UserSerializer(read_only=True) # Nested user details
    seller_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(user_type__in=['seller', 'manufacturer']),
        source='seller', write_only=True
    )
    category = CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(), source='category', write_only=True, allow_null=True
    )
    tags = TagSerializer(many=True, read_only=True)
    tag_ids = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), source='tags', write_only=True, many=True, required=False
    )
    certifications = CertificationSerializer(many=True, read_only=True)
    certification_ids = serializers.PrimaryKeyRelatedField(
        queryset=Certification.objects.all(), source='certifications', write_only=True, many=True, required=False
    )
    main_image_url = serializers.ImageField(source='main_image', read_only=True)


    class Meta:
        model = Material
        fields = [
            'id', 'seller', 'seller_id', 'name', 'slug', 'description', 'category', 'category_id',
            'tags', 'tag_ids', 'is_active', 'is_verified', 'main_image', 'main_image_url', 'additional_images',
            'certifications', 'certification_ids', 'price_per_unit', 'unit',
            'minimum_order_quantity', 'stock_quantity', 'sku', 'composition',
            'weight_gsm', 'width_cm', 'country_of_origin', 'lead_time_days',
            'created_at', 'updated_at'
        ]
        read_only_fields = ('slug', 'is_verified', 'created_at', 'updated_at', 'main_image_url')
        extra_kwargs = {
            'main_image': {'write_only': True, 'required': False},
        }

    def create(self, validated_data):
        # DRF handles many-to-many for PrimaryKeyRelatedField automatically if 'tags' and 'certifications' are the source
        # For seller_id and category_id, they are automatically handled by source='seller' and source='category'
        return super().create(validated_data)

    def update(self, instance, validated_data):
        return super().update(instance, validated_data)

class DesignSerializer(serializers.ModelSerializer):
    designer = UserSerializer(read_only=True)
    designer_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(user_type='designer'),
        source='designer', write_only=True
    )
    category = CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(), source='category', write_only=True, allow_null=True
    )
    tags = TagSerializer(many=True, read_only=True)
    tag_ids = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), source='tags', write_only=True, many=True, required=False
    )
    certifications = CertificationSerializer(many=True, read_only=True)
    certification_ids = serializers.PrimaryKeyRelatedField(
        queryset=Certification.objects.all(), source='certifications', write_only=True, many=True, required=False
    )
    tech_packs = TechPackSerializer(many=True, read_only=True)
    thumbnail_image_url = serializers.ImageField(source='thumbnail_image', read_only=True)


    class Meta:
        model = Design
        fields = [
            'id', 'designer', 'designer_id', 'title', 'slug', 'description', 'category', 'category_id',
            'tags', 'tag_ids', 'is_active', 'is_verified', 'thumbnail_image', 'thumbnail_image_url',
            'certifications', 'certification_ids', 'price', 'licensing_terms',
            'design_files_link', 'tech_packs',
            'created_at', 'updated_at'
        ]
        read_only_fields = ('slug', 'is_verified', 'created_at', 'updated_at', 'thumbnail_image_url')
        extra_kwargs = {
            'thumbnail_image': {'write_only': True, 'required': False},
        }