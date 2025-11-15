from django.contrib import admin
from .models import Category, Product, CourseFile, Instructor, Chapter, Video


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name', 'description')


@admin.register(Instructor)
class InstructorAdmin(admin.ModelAdmin):
    list_display = ('name', 'email')
    search_fields = ('name', 'email', 'bio')


class CourseFileInline(admin.TabularInline):
    model = CourseFile
    extra = 0
    fields = ('title', 'file', 'file_type', 'chapter')


class ChapterInline(admin.TabularInline):
    model = Chapter
    extra = 0
    fields = ('title', 'description', 'order')


class VideoInline(admin.TabularInline):
    model = Video
    extra = 0
    fields = ('title', 'chapter', 'video_file', 'video_url', 'duration', 'order', 'is_preview')



@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        'title', 'instructors_display', 'price', 'course_type', 
        'category', 'start_date', 'registration_deadline', 'is_registration_open'
    )
    list_filter = ('course_type', 'category', 'start_date')
    search_fields = ('title', 'description', 'instructors__name')
    filter_horizontal = ('instructors',)
    fieldsets = (
        ('اطلاعات پایه', {
            'fields': ('title', 'category', 'description', 'price', 'duration', 'image')
        }),
        ('مدرسین', {
            'fields': ('instructors',),
            'description': 'می‌توانید چند مدرس انتخاب کنید.'
        }),
        ('نوع دوره', {
            'fields': ('course_type', 'start_date', 'end_date')
        }),
        ('محدودیت‌ها', {
            'fields': ('registration_deadline', 'access_expiration'),
        }),
    )

    def get_inline_instances(self, request, obj=None):
        if not obj:
            return []
        if obj.course_type == 'offline':
            inlines = [ChapterInline, VideoInline, CourseFileInline]
        else:
            inlines = [CourseFileInline]
        return [inline(self.model, self.admin_site) for inline in inlines]

    def instructors_display(self, obj):
        return obj.get_instructors_display()
    instructors_display.short_description = 'مدرس(ها)'

    def is_registration_open(self, obj):
        return obj.is_registration_open()
    is_registration_open.boolean = True
    is_registration_open.short_description = 'ثبت‌نام باز است'



@admin.register(Chapter)
class ChapterAdmin(admin.ModelAdmin):
    list_display = ('product', 'title', 'order')
    list_filter = ('product',)
    search_fields = ('title', 'product__title')
    ordering = ('product', 'order')


@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = ('product', 'title', 'chapter', 'duration', 'order', 'is_preview')
    list_filter = ('product', 'chapter', 'is_preview')
    search_fields = ('title', 'product__title')
    ordering = ('product', 'order')


@admin.register(CourseFile)
class CourseFileAdmin(admin.ModelAdmin):
    list_display = ('product', 'title', 'file_type', 'chapter')
    list_filter = ('file_type', 'product__course_type')
    search_fields = ('title', 'product__title')
