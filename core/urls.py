from django.urls import path
from . import views

urlpatterns = [
    # ====== HALAMAN PUBLIK ======
    path('', views.home, name='home'),
    path('legalitas/', views.legalitas_public, name='legalitas_public'),
    path('arsip/', views.report_archive, name='report_archive'),
    path('arsip/hapus/<int:pk>/', views.report_delete_from_archive, name='report_delete_from_archive'),

# ====== DONASI (Publik + Admin) ======
path('donasi/', views.donation_page, name='donation_page'),
path('donasi/upload/<str:dtype>/', views.donation_proof_upload, name='donation_proof_upload'),

# Admin list & hapus bukti
path('donasi/admin/', views.donation_proof_admin, name='donation_proof_admin'),
path('donasi/admin/<int:pk>/hapus/', views.donation_proof_delete, name='donation_proof_delete'),

    # ====== LAPORAN PUBLIK ======
    path('r/<int:pk>/', views.report_public_detail, name='report_public_detail'),
    path('r/<int:pk>/pdf/', views.report_pdf_inline, name='report_pdf_inline'),
    path('r/<int:pk>/<slug:sheet>/', views.report_public_sheet, name='report_public_sheet'),
    path('r/<int:pk>/<slug:sheet>/csv/', views.report_public_export_csv, name='report_public_export_csv'),

    # ====== AUTH (LOGIN / LOGOUT) ======
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.do_logout, name='logout'),

    # ====== PANEL PENGURUS ======
    path('dashboard/', views.dashboard, name='dashboard'),
    path('profil/', views.mosque_profile, name='mosque_profile'),

    # ====== DOKUMEN LEGALITAS ======
    path('dokumen/upload/', views.document_upload, name='document_upload'),
    path('dokumen/<int:pk>/hapus/', views.document_delete, name='document_delete'),

    # ====== MASTER DATA ======
    path('pengurus/add/', views.management_add, name='management_add'),
    path('program/add/', views.program_add, name='program_add'),
    path('donatur/add/', views.donor_add, name='donor_add'),
    path('channel/add/', views.channel_add, name='channel_add'),

    # ✅ Tambahan baru — hapus pengurus & program
    path('pengurus/<int:pk>/hapus/', views.management_delete, name='management_delete'),
    path('program/<int:pk>/hapus/', views.program_delete, name='program_delete'),

    # ====== LAPORAN KEUANGAN (PANEL) ======
    path('laporan/upload/', views.report_upload, name='report_upload'),
    path('laporan/<int:pk>/', views.report_detail, name='report_detail'),
    path('laporan/<int:pk>/sheet/<slug:sheet>/', views.report_sheet, name='report_sheet'),
    path('laporan/<int:pk>/sheet/<slug:sheet>/csv/', views.report_export_csv, name='report_export_csv'),
    path('laporan/<int:pk>/hapus/', views.report_delete, name='report_delete'),
]
