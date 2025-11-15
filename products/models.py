from django.db import models
from django.utils import timezone

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = 'دسته‌بندی'
        verbose_name_plural = 'دسته‌بندی‌ها'

    def __str__(self):
        return self.name

class Instructor(models.Model):
    name = models.CharField(max_length=100)
    bio = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='instructors/images/', null=True, blank=True)
    email = models.EmailField(null=True, blank=True, unique=True)

    class Meta:
        verbose_name = 'مدرس'
        verbose_name_plural = 'مدرسین'

    def __str__(self):
        return self.name

class Product(models.Model):
    COURSE_TYPE_CHOICES = [
        ('online', 'آنلاین'),
        ('offline', 'آفلاین'),
    ]

    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    title = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    instructors = models.ManyToManyField(Instructor, related_name='products', blank=True)
    instructor = models.CharField(max_length=100, blank=True, null=True)
    duration = models.CharField(max_length=50)
    course_type = models.CharField(max_length=10, choices=COURSE_TYPE_CHOICES)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    image = models.ImageField(upload_to='products/images/', null=True, blank=True)
    registration_deadline = models.DateField(null=True, blank=True)
    access_expiration = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'دوره'
        verbose_name_plural = 'دوره‌ها'

    def __str__(self):
        return f"{self.title} ({self.get_course_type_display()})"

    def get_instructors_display(self):
        if self.instructors.exists():
            return ", ".join([i.name for i in self.instructors.all()])
        return self.instructor or "نامشخص"

    def is_registration_open(self):
        if self.course_type == 'online' and self.registration_deadline:
            return timezone.now().date() <= self.registration_deadline
        return True

class Chapter(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='chapters', limit_choices_to={'course_type': 'offline'})
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'created_at']
        verbose_name = 'فصل'
        verbose_name_plural = 'فصل‌ها'

    def __str__(self):
        return f"{self.product.title} - {self.title}"

class Video(models.Model):
    chapter = models.ForeignKey(Chapter, on_delete=models.CASCADE, related_name='videos', null=True, blank=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='videos', limit_choices_to={'course_type': 'offline'})
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    video_file = models.FileField(upload_to='course_videos/', null=True, blank=True)
    video_url = models.URLField(null=True, blank=True)
    duration = models.PositiveIntegerField(null=True, blank=True)
    order = models.PositiveIntegerField(default=0)
    is_preview = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'created_at']
        verbose_name = 'ویدیو'
        verbose_name_plural = 'ویدیوها'

    def __str__(self):
        return f"{self.product.title} - {self.title}"

class CourseFile(models.Model):
    FILE_TYPE_CHOICES = [
        ('exercise', 'تمرین'),
        ('pdf', 'PDF'),
        ('code', 'کد'),
        ('other', 'سایر'),
    ]
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='files')
    chapter = models.ForeignKey(Chapter, on_delete=models.CASCADE, related_name='files', null=True, blank=True)
    title = models.CharField(max_length=200)
    file = models.FileField(upload_to='course_files/')
    file_type = models.CharField(max_length=10, choices=FILE_TYPE_CHOICES, default='other')
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']
        verbose_name = 'فایل دوره'
        verbose_name_plural = 'فایل‌های دوره'

    def __str__(self):
        return f"{self.product.title} - {self.title}"

