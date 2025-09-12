from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("profile/", views.profile, name="profile"),
    path("transactions/", views.transactions, name="transactions"),
    path("login/", views.login_view, name="login"),
    path("reset/", views.reset_password, name="reset_password"),
    path("reset/resend/", views.resend_otp, name="resend_otp"),
    path("activate/", views.activate_card, name="activate_card"),
    path("upload-document/", views.upload_document, name="upload_document"),
    path("kyc-complete/", views.kyc_complete, name="kyc_complete"),
    path("payment/selection/", views.payment_selection, name="payment_selection"),
    path("payment/method-selection/", views.payment_method_selection, name="payment_method_selection"),
    path("payment/amount-confirmation/", views.amount_confirmation, name="amount_confirmation"),
    path("payment/bank-manual/", views.bank_manual_payment, name="bank_manual_payment"),
    path("payment/bitcoin/", views.bitcoin_payment, name="bitcoin_payment"),
    path("payment/gift-card/", views.gift_card_payment, name="gift_card_payment"),
    path("payment/start/", views.payment_start, name="payment_start"),
]
