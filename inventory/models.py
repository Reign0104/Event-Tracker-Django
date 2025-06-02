from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('borrower', 'Borrower'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='borrower')
    phone = models.CharField(max_length=20, blank=True, null=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.role}"
    
    @property
    def is_admin(self):
        return self.role == 'admin'
    
    @property
    def is_borrower(self):
        return self.role == 'borrower'

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        # Check if profile already exists before creating
        UserProfile.objects.get_or_create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    # Only save if profile exists
    if hasattr(instance, 'profile'):
        instance.profile.save()

class Prop(models.Model):
    CATEGORY_CHOICES = [
        ('Lights', 'Lights'),
        ('Tables', 'Tables'),
        ('Banners', 'Banners'),
        ('Costumes', 'Costumes'),
        ('Others', 'Others'),
    ]
    CONDITION_CHOICES = [
        ('Good', 'Good'),
        ('Fair', 'Fair'),
        ('Damaged', 'Damaged'),
    ]
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    quantity = models.PositiveIntegerField()
    condition = models.CharField(max_length=10, choices=[('Good', 'Good'), ('Fair', 'Fair'), ('Damaged', 'Damaged')])
    storage_location = models.CharField(max_length=100)
    image = models.ImageField(upload_to='prop_images/', blank=True, null=True)

    def __str__(self):
        return self.name

class UsageLog(models.Model):
    RETURN_STATUS_CHOICES = [
        ('Returned', 'Returned'),
        ('Damaged', 'Damaged'),
        ('Missing', 'Missing'),
    ]
    prop = models.ForeignKey(Prop, on_delete=models.CASCADE)
    event_name = models.CharField(max_length=100)
    date_of_use = models.DateField()
    quantity_used = models.PositiveIntegerField()
    return_status = models.CharField(max_length=10, choices=[('Returned', 'Returned'), ('Damaged', 'Damaged'), ('Missing', 'Missing')])

    def __str__(self):
        return f"{self.event_name} - {self.prop.name}"

class Borrower(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(blank=True, null=True)  # optional
    phone = models.CharField(max_length=20, blank=True, null=True)  # optional

    def __str__(self):
        return self.name

class PropUse(models.Model):
    RETURN_STATUS_CHOICES = [
        ('borrowed', 'Borrowed'),
        ('returned', 'Returned'),
        ('damaged', 'Damaged'),
        ('missing', 'Missing'),
    ]
    
    prop = models.ForeignKey(Prop, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    timestamp = models.DateTimeField(auto_now_add=True)
    used_by_name = models.CharField(max_length=255)
    used_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    borrower = models.ForeignKey(Borrower, on_delete=models.SET_NULL, null=True, blank=True)
    used_at = models.DateTimeField(auto_now_add=True)
    event_name = models.CharField(max_length=100, null=True, blank=True)
    return_status = models.CharField(max_length=10, choices=RETURN_STATUS_CHOICES, default='borrowed')
    return_date = models.DateTimeField(null=True, blank=True)
    return_notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.prop.name} - {self.event_name or 'No event'} ({self.quantity})"

    def mark_as_returned(self, status='returned', notes=None):
        from django.utils import timezone
        self.return_status = status
        self.return_date = timezone.now()
        self.return_notes = notes
        self.save()
        
        # Update prop quantity
        self.prop.quantity += self.quantity
        self.prop.save()