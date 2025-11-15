from rest_framework import serializers
from .models import Category, Product, CourseFile

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'description']

class CourseFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = CourseFile
        fields = ['id', 'title', 'file']

class ProductSerializer(serializers.ModelSerializer):
    category = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all())
    files = CourseFileSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = [
            'id', 'title', 'description', 'price', 'instructor', 'duration',
            'course_type', 'start_date', 'end_date', 'image', 'registration_deadline',
            'access_expiration', 'category', 'files', 'created_at'
        ]

class ProductListSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)

    class Meta:
        model = Product
        fields = ['id', 'title', 'price', 'instructor', 'duration', 'course_type', 'category']