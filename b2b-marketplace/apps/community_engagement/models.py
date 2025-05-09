import uuid
from django.db import models
from django.conf import settings
from django.utils.text import slugify
from apps.core.models import AbstractBaseModel # For created_at, updated_at
# from taggit.managers import TaggableManager # Optional: for tagging forum posts/threads

# If AbstractBaseModel is not defined:
# class AbstractBaseModel(models.Model):
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)
#     class Meta:
#         abstract = True

class ForumCategory(AbstractBaseModel):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    description = models.TextField(blank=True, null=True)
    # icon = models.CharField(max_length=50, blank=True, null=True) # e.g., Font Awesome class

    class Meta:
        verbose_name_plural = "Forum Categories"
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class ForumThread(AbstractBaseModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    category = models.ForeignKey(ForumCategory, on_delete=models.CASCADE, related_name='threads')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='forum_threads')
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=270, unique=True, blank=True, editable=False)
    is_pinned = models.BooleanField(default=False, help_text="Pinned threads appear at the top.")
    is_locked = models.BooleanField(default=False, help_text="Locked threads cannot receive new posts.")
    views_count = models.PositiveIntegerField(default=0)
    # tags = TaggableManager(blank=True) # If using django-taggit

    class Meta:
        ordering = ['-is_pinned', '-updated_at'] # Pinned first, then by last activity (updated_at of thread or last post)

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)
            slug = base_slug
            counter = 1
            while ForumThread.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    def get_reply_count(self):
        return self.posts.count() -1 # Exclude the initial post if it's part of posts

    def get_last_post_author(self):
        last_post = self.posts.order_by('-created_at').first()
        return last_post.author if last_post else None

    def get_last_post_created_at(self):
        last_post = self.posts.order_by('-created_at').first()
        return last_post.created_at if last_post else self.updated_at


class ForumPost(AbstractBaseModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    thread = models.ForeignKey(ForumThread, on_delete=models.CASCADE, related_name='posts')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='forum_posts')
    content = models.TextField()
    is_edited = models.BooleanField(default=False)
    # parent_post = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies') # For threaded replies within a post

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Post by {self.author.username} in '{self.thread.title}' (ID: {self.id})"

    def save(self, *args, **kwargs):
        is_new = self._state.adding
        if not is_new and self.pk: # if object is being updated
            self.is_edited = True
        super().save(*args, **kwargs)
        if is_new: # Update thread's updated_at timestamp on new post
            self.thread.updated_at = self.created_at
            self.thread.save(update_fields=['updated_at'])


# --- Portfolio/Showcase ---
class Showcase(AbstractBaseModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='showcases')
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True, editable=False)
    description = models.TextField(blank=True, null=True)
    cover_image = models.ImageField(upload_to='showcases/covers/', blank=True, null=True)
    is_public = models.BooleanField(default=True)
    # tags = TaggableManager(blank=True) # If using django-taggit

    class Meta:
        ordering = ['-created_at']
        unique_together = ('user', 'slug') # User can't have two showcases with same slug

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)
            slug = base_slug
            counter = 1
            # Ensure slug is unique for this user
            while Showcase.objects.filter(user=self.user, slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.title} by {self.user.username}"


class ShowcaseItem(AbstractBaseModel):
    showcase = models.ForeignKey(Showcase, on_delete=models.CASCADE, related_name='items')
    title = models.CharField(max_length=200, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='showcases/items/', blank=True, null=True)
    file = models.FileField(upload_to='showcases/files/', blank=True, null=True, help_text="e.g., PDF, Design file")
    url_link = models.URLField(blank=True, null=True, help_text="Link to external project or item")
    item_type = models.CharField(max_length=50, default='image', choices=(('image', 'Image'), ('file', 'File'), ('link', 'Link')))
    order = models.PositiveIntegerField(default=0, help_text="Order of item in showcase")

    class Meta:
        ordering = ['showcase', 'order', 'created_at']

    def __str__(self):
        return self.title or f"Item for {self.showcase.title}"