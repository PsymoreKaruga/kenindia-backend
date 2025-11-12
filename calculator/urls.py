from django.urls import path
from . import views

urlpatterns = [
    path('calculate/premium/', views.calculate_premium, name='calculate_premium'),
    path('calculate/sum-assured/', views.calculate_sum_assured, name='calculate_sum_assured'),
    path("mpesa/stk_push/", views.stk_push_view, name="stk_push"),
    # legacy / external clients may call 'stkpush' without underscore — keep an alias for compatibility
    path("mpesa/stkpush/", views.stk_push_view, name="stk_push_alias"),
    path("mpesa/callback/", views.stk_callback_view, name="stk_callback"),
    path('calculate/status/<int:calc_id>/', views.check_calculation_status, name='check_calc_status'),
    path('calculate/download/<int:calc_id>/', views.download_result, name='download_result'),
    path('generate-pdf/', views.generate_pdf_quotation, name='generate_pdf'),
]
