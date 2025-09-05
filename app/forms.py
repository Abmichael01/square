from django import forms

from .models import User


class AdminUserCreationForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("email", "card_amount", "is_staff", "is_active")

    def save(self, commit: bool = True):
        user: User = super().save(commit=False)
        # Create without a password; user will set it via the OTP reset flow
        user.set_unusable_password()
        if commit:
            user.save()
            # ManyToMany (groups/permissions) handled after save if needed
        return user


class AdminUserChangeForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("email", "card_amount", "is_staff", "is_active", "groups", "user_permissions")


