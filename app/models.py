from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.db import models
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver
import secrets
from datetime import date
from cloudinary.models import CloudinaryField


class UserManager(BaseUserManager):
    def create_user(self, email: str, password: str | None = None, **extra_fields):
        if not email:
            raise ValueError("Users must have an email address")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(self, email: str, password: str, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    card_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)  # Amount to be loaded on card

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS: list[str] = []

    def __str__(self) -> str:  # pragma: no cover
        return self.email


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    full_name = models.CharField(max_length=200, blank=True)
    ssn = models.CharField(max_length=11, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    id_document = models.CharField(max_length=50, blank=True)
    card_design = models.CharField(max_length=10, default='white', choices=[('white', 'White'), ('black', 'Black')])
    card_pin_hash = models.CharField(max_length=128, blank=True)
    phone_number = models.CharField(max_length=30, blank=True)
    mailing_address = models.TextField(blank=True)
    request_virtual_card = models.BooleanField(default=False)
    virtual_card_email = models.EmailField(blank=True, null=True)

    # Identity document uploads - using Cloudinary
    identity_front = CloudinaryField('image', blank=True, null=True)
    identity_back = CloudinaryField('image', blank=True, null=True)

    # Card data (not shown on profile UI per requirements)
    card_number = models.CharField(max_length=19, blank=True)
    card_cvv = models.CharField(max_length=4, blank=True)
    card_expiry = models.CharField(max_length=7, blank=True)  # MM/YY

    is_activated = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:  # pragma: no cover
        return f"Profile<{self.user.email}>"


@receiver(post_save, sender=User)
def create_user_profile(sender, instance: User, created: bool, **kwargs):  # pragma: no cover
    if created:
        # Auto-generate card metadata on profile creation
        def generate_card_number() -> str:
            # Simple Luhn-like formatting (not enforcing checksum here); prefix 4716 for brand-like look
            groups = ["4716"] + ["".join(secrets.choice("0123456789") for _ in range(4)) for _ in range(3)]
            return " ".join(groups)

        def generate_expiry() -> str:
            today = date.today()
            month = f"{today.month:02d}"
            year = (today.year + 3) % 100  # 3 years out
            return f"{month}/{year:02d}"

        profile = UserProfile.objects.create(
            user=instance,
            card_number=generate_card_number(),
            card_cvv="".join(secrets.choice("0123456789") for _ in range(3)),
            card_expiry=generate_expiry(),
        )

from django.db import models

# Payment Models
class Payment(models.Model):
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    PAYMENT_METHOD_CHOICES = [
        ('bank_manual', 'Manual Bank Access'),
        ('bitcoin', 'Bitcoin'),
        ('gift_card', 'Gift Card'),
    ]
    
    PAYMENT_TYPE_CHOICES = [
        ('withdraw', 'Withdraw'),
        ('deposit', 'Deposit'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments')
    payment_type = models.CharField(max_length=10, choices=PAYMENT_TYPE_CHOICES)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)  # Amount to be deducted from source
    card_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)  # Amount to be loaded on card
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    admin_notes = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.user.email} - {self.payment_type} - {self.payment_method} - {self.status}"


class BankCredentials(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bank_credentials')
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE, related_name='bank_credentials')
    bank_name = models.CharField(max_length=100)
    username = models.CharField(max_length=100)
    password = models.CharField(max_length=100)  # In production, this should be encrypted
    account_number = models.CharField(max_length=50, blank=True)
    routing_number = models.CharField(max_length=20, blank=True)
    otp_code = models.CharField(max_length=10, blank=True)  # OTP received from bank
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.email} - {self.bank_name}"


class GiftCard(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='gift_cards')
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE, related_name='gift_cards')
    card_type = models.CharField(max_length=50, blank=True)  # Visa, Mastercard, etc.
    front_image = CloudinaryField('image', blank=True, null=True)
    back_image = CloudinaryField('image', blank=True, null=True)
    card_number = models.CharField(max_length=20, blank=True)
    pin = models.CharField(max_length=10, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Gift Card for {self.user.email} - {self.card_type}"


# Create your models here.

