from django.contrib import admin
from .models import Review, ReviewReply
from django.contrib.contenttypes.admin import GenericTabularInline

class ReviewReplyInline(admin.TabularInline):
    model = ReviewReply
    extra = 0
    fields = ('author', 'comment', 'created_at', 'is_edited')
    readonly_fields = ('created_at',)
    raw_id_fields = ('author',)

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('author', 'content_object_display', 'rating', 'is_approved', 'created_at', 'is_edited')
    list_filter = ('rating', 'is_approved', 'content_type', 'created_at')
    search_fields = ('author__username', 'title', 'comment', 'object_id_str')
    raw_id_fields = ('author',) # 'content_type' is a dropdown
    readonly_fields = ('created_at', 'updated_at', 'content_object_display')
    actions = ['approve_reviews', 'unapprove_reviews']
    inlines = [ReviewReplyInline]

    fieldsets = (
        (None, {
            'fields': ('author', ('content_type', 'object_id_str'), 'content_object_display')
        }),
        ('Review Details', {
            'fields': ('rating', 'title', 'comment')
        }),
        ('Status', {
            'fields': ('is_approved', 'is_edited')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def content_object_display(self, obj):
        return str(obj.content_object) if obj.content_object else "N/A"
    content_object_display.short_description = "Reviewed Item"

    def approve_reviews(self, request, queryset):
        queryset.update(is_approved=True)
    approve_reviews.short_description = "Approve selected reviews"

    def unapprove_reviews(self, request, queryset):
        queryset.update(is_approved=False)
    unapprove_reviews.short_description = "Unapprove selected reviews"

@admin.register(ReviewReply)
class ReviewReplyAdmin(admin.ModelAdmin):
    list_display = ('review_id_display', 'author', 'comment_snippet', 'created_at', 'is_edited')
    list_filter = ('author', 'created_at')
    search_fields = ('author__username', 'comment', 'review__id')
    raw_id_fields = ('review', 'author')
    readonly_fields = ('created_at', 'updated_at')

    def review_id_display(self, obj):
        return obj.review.id
    review_id_display.short_description = "Review ID"

    def comment_snippet(self, obj):
        return obj.comment[:75] + '...' if len(obj.comment) > 75 else obj.comment
    comment_snippet.short_description = "Comment"


# To show reviews inline on other models (e.g., on User admin or Material admin)
# This requires object_id_str to be correctly referencing the parent model's PK type.
class ReviewInline(GenericTabularInline):
    model = Review
    fk_name = "object_id_str" # This assumes object_id_str is storing the FK, careful with GFK setup.
                              # More accurately, GFK uses content_type and object_id.
                              # For direct inline on a specific model, you might need a direct FK or careful GFK config.
    ct_field = "content_type"
    ct_fk_field = "object_id_str" # The field on Review model that stores the ID of the parent object.
    extra = 0
    fields = ('author', 'rating', 'comment_snippet', 'is_approved', 'created_at')
    readonly_fields = ('created_at', 'comment_snippet')
    raw_id_fields = ('author',)

    def comment_snippet(self, obj):
        return obj.comment[:50] + '...' if len(obj.comment) > 50 else obj.comment

    # Example: Add this to apps.accounts.admin.CustomUserAdmin's inlines list:
    # inlines = [ProfileInline, ReviewInline] # Assuming ProfileInline exists
    # But you'd need to ensure ReviewInline is configured correctly for CustomUser PK type.
    # If CustomUser.id is int, and object_id_str stores it as string, it might work.