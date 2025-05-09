from django.contrib import admin
from .models import ForumCategory, ForumThread, ForumPost, Showcase, ShowcaseItem

@admin.register(ForumCategory)
class ForumCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'description')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name', 'description')

class ForumPostInline(admin.TabularInline):
    model = ForumPost
    extra = 1
    fields = ('author', 'content_excerpt', 'created_at', 'is_edited')
    readonly_fields = ('created_at', 'content_excerpt')
    raw_id_fields = ('author',)

    def content_excerpt(self, obj):
        return obj.content[:75] + '...' if len(obj.content) > 75 else obj.content
    content_excerpt.short_description = 'Content Excerpt'

@admin.register(ForumThread)
class ForumThreadAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'author', 'is_pinned', 'is_locked', 'views_count', 'slug', 'created_at', 'updated_at') # Added slug to list_display for visibility
    list_filter = ('category', 'is_pinned', 'is_locked', 'author')
    search_fields = ('title', 'author__username', 'category__name', 'slug') # Added slug to search_fields
    # prepopulated_fields = {'slug': ('title',)} # <--- REMOVE OR COMMENT OUT THIS LINE
    raw_id_fields = ('category', 'author')
    readonly_fields = ('views_count', 'updated_at', 'slug') # Add 'slug' to readonly_fields if you want to see it on the change form but not edit it
    inlines = [ForumPostInline]


@admin.register(ForumPost)
class ForumPostAdmin(admin.ModelAdmin):
    list_display = ('id', 'thread_title_display', 'author', 'content_excerpt', 'created_at', 'is_edited')
    list_filter = ('thread__category', 'author', 'is_edited')
    search_fields = ('content', 'author__username', 'thread__title')
    raw_id_fields = ('thread', 'author')
    readonly_fields = ('thread_title_display',)

    def thread_title_display(self, obj):
        return obj.thread.title
    thread_title_display.short_description = 'Thread'

    def content_excerpt(self, obj):
        return obj.content[:75] + '...' if len(obj.content) > 75 else obj.content
    content_excerpt.short_description = 'Content'


class ShowcaseItemInline(admin.TabularInline):
    model = ShowcaseItem
    extra = 1
    fields = ('title', 'item_type', 'image', 'file', 'url_link', 'order')
    ordering = ('order',)

@admin.register(Showcase)
class ShowcaseAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'is_public', 'slug', 'created_at') # Added slug
    list_filter = ('is_public', 'user')
    search_fields = ('title', 'description', 'user__username', 'slug') # Added slug
    # prepopulated_fields = {'slug': ('title',)} # <--- REMOVE OR COMMENT OUT
    raw_id_fields = ('user',)
    readonly_fields = ('slug',) # Add slug here
    inlines = [ShowcaseItemInline]

@admin.register(ShowcaseItem)
class ShowcaseItemAdmin(admin.ModelAdmin):
    list_display = ('title', 'showcase_title_display', 'item_type', 'order', 'created_at')
    list_filter = ('item_type', 'showcase__user')
    search_fields = ('title', 'description', 'showcase__title')
    raw_id_fields = ('showcase',)

    def showcase_title_display(self, obj):
        return obj.showcase.title
    showcase_title_display.short_description = 'Showcase'