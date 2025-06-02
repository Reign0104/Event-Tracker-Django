from django.contrib import admin
from .models import Prop, UsageLog, PropUse, Borrower, UserProfile
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

# Inline for UserProfile
class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'

# Extend User admin
class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'get_role')
    list_select_related = ('profile',)

    def get_role(self, instance):
        return instance.profile.role
    get_role.short_description = 'Role'

# Unregister and re-register User with new admin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)

@admin.register(Prop)
class PropAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'quantity', 'condition', 'storage_location')
    list_filter = ('category', 'condition')
    search_fields = ('name', 'category', 'storage_location')

@admin.register(UsageLog)
class UsageLogAdmin(admin.ModelAdmin):
    list_display = ('prop', 'event_name', 'date_of_use', 'quantity_used', 'return_status')
    list_filter = ('return_status', 'date_of_use')
    search_fields = ('prop__name', 'event_name')

@admin.register(PropUse)
class PropUseAdmin(admin.ModelAdmin):
    list_display = ('prop', 'quantity', 'event_name', 'used_by_name', 'timestamp')
    list_filter = ('prop', 'timestamp')
    search_fields = ('prop__name', 'event_name', 'used_by_name')

@admin.register(Borrower)
class BorrowerAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone')
    search_fields = ('name', 'email', 'phone')

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'phone')
    list_filter = ('role',)
    search_fields = ('user__username', 'phone')
