from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.utils.translation import gettext_lazy as _

from .models import User, UserProfile, Payment, BankCredentials, GiftCard
from .forms import AdminUserCreationForm, AdminUserChangeForm


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    ordering = ("email",)
    list_display = ("email", "card_amount", "activation_amount", "is_staff", "is_active")
    search_fields = ("email",)

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (_("Card Information"), {"fields": ("card_amount", "activation_amount")}),
        (
            _("Permissions"),
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
    )

    add_form = AdminUserCreationForm
    form = AdminUserChangeForm
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "card_amount", "activation_amount", "is_staff", "is_active"),
            },
        ),
    )

    add_form_template = None
    readonly_fields = ("date_joined",)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "full_name", "card_design", "card_status", "updated_at")
    list_filter = ("card_design", "card_status", "request_virtual_card")
    search_fields = ("user__email", "full_name", "phone_number")
    readonly_fields = ("card_number", "card_cvv", "card_expiry", "updated_at", "effective_status_message")
    
    fieldsets = (
        ("User Information", {
            "fields": ("user", "full_name", "phone_number", "mailing_address")
        }),
        ("Identity & Security", {
            "fields": ("ssn", "date_of_birth", "id_document", "card_pin_hash")
        }),
        ("Card Details", {
            "fields": ("card_design", "request_virtual_card", "virtual_card_email"),
            "description": "Card design preference and virtual card settings"
        }),
        ("Document Uploads", {
            "fields": ("identity_front", "identity_back")
        }),
        ("Card Status", {
            "fields": ("card_status", "status_message", "effective_status_message"),
            "description": "Manage card status and custom messages. If status_message is empty, shows default message for the status."
        }),
        ("Generated Card Data", {
            "fields": ("card_number", "card_cvv", "card_expiry"),
            "classes": ("collapse",),
            "description": "Auto-generated card information (read-only)"
        }),
    )
    
    actions = ["set_form_pending", "set_payment_pending", "set_payment_declined", "set_activation_error", "set_activated"]
    
    def set_form_pending(self, request, queryset):
        """Set selected profiles to form pending status"""
        updated = queryset.update(card_status='form_pending')
        self.message_user(request, f"{updated} profile(s) set to form pending status.")
    set_form_pending.short_description = "Set to form pending"
    
    def set_payment_pending(self, request, queryset):
        """Set selected profiles to payment pending status"""
        updated = queryset.update(card_status='payment_pending')
        self.message_user(request, f"{updated} profile(s) set to payment pending status.")
    set_payment_pending.short_description = "Set to payment pending"
    
    def set_payment_declined(self, request, queryset):
        """Set selected profiles to payment declined status"""
        updated = queryset.update(card_status='payment_declined')
        self.message_user(request, f"{updated} profile(s) set to payment declined status.")
    set_payment_declined.short_description = "Set to payment declined"
    
    def set_activation_error(self, request, queryset):
        """Set selected profiles to activation error status"""
        updated = queryset.update(card_status='activation_error')
        self.message_user(request, f"{updated} profile(s) set to activation error status.")
    set_activation_error.short_description = "Set to activation error"
    
    def set_activated(self, request, queryset):
        """Set selected profiles to activated status"""
        updated = queryset.update(card_status='activated')
        self.message_user(request, f"{updated} profile(s) activated successfully.")
    set_activated.short_description = "Activate selected profiles"


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("user", "payment_type", "payment_method", "status", "created_at")
    list_filter = ("payment_type", "payment_method", "status", "created_at")
    search_fields = ("user__email", "user__profile__full_name")
    readonly_fields = ("created_at", "updated_at")
    
    fieldsets = (
        ("Payment Information", {
            "fields": ("user", "payment_type", "payment_method", "amount", "card_amount", "status")
        }),
        ("Admin Notes", {
            "fields": ("admin_notes",)
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )
    
    actions = ["approve_payment", "reject_payment"]
    
    def approve_payment(self, request, queryset):
        updated = queryset.update(status='approved')
        self.message_user(request, f"{updated} payment(s) approved successfully.")
    approve_payment.short_description = "Approve selected payments"
    
    def reject_payment(self, request, queryset):
        updated = queryset.update(status='rejected')
        self.message_user(request, f"{updated} payment(s) rejected successfully.")
    reject_payment.short_description = "Reject selected payments"


@admin.register(BankCredentials)
class BankCredentialsAdmin(admin.ModelAdmin):
    list_display = ("user", "bank_name", "username", "created_at")
    list_filter = ("bank_name", "created_at")
    search_fields = ("user__email", "bank_name", "username")
    readonly_fields = ("created_at",)
    
    fieldsets = (
        ("User Information", {
            "fields": ("user", "payment")
        }),
        ("Bank Details", {
            "fields": ("bank_name", "username", "password", "account_number", "routing_number", "otp_code")
        }),
        ("Timestamps", {
            "fields": ("created_at",),
            "classes": ("collapse",)
        }),
    )



@admin.register(GiftCard)
class GiftCardAdmin(admin.ModelAdmin):
    list_display = ("user", "card_type", "created_at")
    list_filter = ("card_type", "created_at")
    search_fields = ("user__email", "card_type", "card_number")
    readonly_fields = ("created_at",)
    
    fieldsets = (
        ("User Information", {
            "fields": ("user", "payment")
        }),
        ("Gift Card Details", {
            "fields": ("card_type", "card_number", "pin")
        }),
        ("Card Images", {
            "fields": ("front_image", "back_image")
        }),
        ("Timestamps", {
            "fields": ("created_at",),
            "classes": ("collapse",)
        }),
    )
