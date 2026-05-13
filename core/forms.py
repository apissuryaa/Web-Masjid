from django import forms
from .models import (
    Mosque, Document, Management, Program, Donor,
    ReportFile, DonationChannel, DonationProof, CashFlow
)
import decimal, re

# ==========================
# FORM MASJID / PROFIL UTAMA
# ==========================
class MosqueForm(forms.ModelForm):
    class Meta:
        model = Mosque
        fields = [
            "name", "address", "city", "province", "established_date",
            "land_status", "deed_number", "npwp", "bank_name", "bank_account",
            "website", "logo_url", "about", "contact_phone", "email",
        ]
        widgets = {
            "about": forms.Textarea(attrs={"rows": 4, "placeholder": "Tulis deskripsi singkat…"}),
            "address": forms.Textarea(attrs={"rows": 2, "placeholder": "Alamat lengkap masjid"}),
            "established_date": forms.DateInput(attrs={"type": "date"}),
            "logo_url": forms.URLInput(attrs={"placeholder": "https://..."}),
            "contact_phone": forms.TextInput(attrs={"placeholder": "08xx-xxxx-xxxx"}),
            "email": forms.EmailInput(attrs={"placeholder": "nama@domain.com"}),
        }
        labels = {
            "name": "Nama Masjid",
            "address": "Alamat",
            "city": "Kota / Kabupaten",
            "province": "Provinsi",
            "established_date": "Tanggal Berdiri",
            "land_status": "Status Tanah",
            "deed_number": "Nomor Akta / Surat Wakaf",
            "npwp": "NPWP",
            "bank_name": "Bank Utama",
            "bank_account": "Nomor Rekening",
            "website": "Website",
            "logo_url": "URL Logo / Foto Masjid",
            "about": "Tentang Masjid",
            "contact_phone": "Nomor Kontak (WA/Telp)",
            "email": "Email Resmi",
        }

# ==========================
# FORM DOKUMEN LEGALITAS
# ==========================
class DocumentForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ['doc_type', 'title', 'file', 'is_public']

# ==========================
# FORM MASTER DATA
# ==========================
class ManagementForm(forms.ModelForm):
    class Meta:
        model = Management
        fields = ['name', 'role', 'phone']

class ProgramForm(forms.ModelForm):
    class Meta:
        model = Program
        fields = ['title', 'description', 'is_active', 'last_update']

class DonorForm(forms.ModelForm):
    class Meta:
        model = Donor
        fields = ['name', 'phone', 'notes', 'is_public']

# ==========================
# FORM LAPORAN KEUANGAN
# ==========================
class ReportUploadForm(forms.ModelForm):
    class Meta:
        model = ReportFile
        fields = ['title', 'file', 'period', 'is_public']

# ==========================
# FORM SALURAN DONASI
# ==========================
class DonationChannelForm(forms.ModelForm):
    class Meta:
        model = DonationChannel
        fields = ['title', 'bank', 'account', 'qris_image', 'is_active']

# ==========================
# FORM BUKTI DONASI (JAMAAH)
# ==========================
from django import forms
from decimal import Decimal, InvalidOperation
from .models import (
    Mosque, Document, Management, Program, Donor,
    ReportFile, DonationChannel, DonationProof
)

# ... class lain tetap ...

class DonationProofForm(forms.ModelForm):
    class Meta:
        model = DonationProof
        fields = ['donation_type', 'donor_name', 'phone', 'amount', 'paid_at', 'note', 'proof', 'is_public']
        widgets = {
            # dikunci lewat URL; user tidak bisa ganti
            'donation_type': forms.HiddenInput(),

            'donor_name': forms.TextInput(attrs={
                'class': 'w-full rounded border px-3 py-2',
                'placeholder': 'Nama lengkap',
            }),
            'phone': forms.TextInput(attrs={
                'class': 'w-full rounded border px-3 py-2',
                'placeholder': '08xxxxxxxxxx',
                'inputmode': 'numeric',
            }),

            # ⚠️ Ganti NumberInput → TextInput supaya boleh titik/koma
            'amount': forms.TextInput(attrs={
                'class': 'w-full rounded border px-3 py-2',
                'placeholder': 'Contoh: 150.000 atau 150.000,50',
                'inputmode': 'decimal',
                'autocomplete': 'off',
            }),

            'paid_at': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full rounded border px-3 py-2'
            }),
            'note': forms.Textarea(attrs={
                'class': 'w-full rounded border px-3 py-2',
                'rows': 3,
                'placeholder': 'Opsional',
            }),
            'proof': forms.ClearableFileInput(attrs={'class': 'w-full rounded border px-3 py-2'}),
        }
        labels = {
            'donation_type': 'Jenis Donasi',
            'donor_name': 'Nama Donatur',
            'phone': 'No. HP/WA',
            'amount': 'Jumlah (Rp)',
            'paid_at': 'Tanggal Transfer',
            'note': 'Catatan',
            'proof': 'Bukti Transfer (jpg/png/pdf)',
            'is_public': 'Tampilkan ke publik?',
        }

    def clean_amount(self):
        """
        Terima input:
          - 150000
          - 150.000
          - 150.000,50
          - 150,5
        Lalu konversi ke Decimal (separator desimal = '.').
        """
        raw = (self.data.get('amount') or '').strip()

        if not raw:
            raise forms.ValidationError('Jumlah wajib diisi.')

        # Hapus spasi dan karakter non-angka kecuali titik/koma
        # Normalisasi: ribuan '.' dihapus; koma jadi titik (desimal)
        normalized = raw.replace(' ', '')
        normalized = normalized.replace('.', '')  # hapus pemisah ribuan
        normalized = normalized.replace(',', '.')  # koma → titik

        try:
            value = Decimal(normalized)
        except (InvalidOperation, ValueError):
            raise forms.ValidationError('Format jumlah tidak valid.')

        # paling banyak 2 angka di belakang koma
        if value.as_tuple().exponent < -2:
            raise forms.ValidationError('Pastikan bilangan tidak memiliki lebih dari 2 angka desimal.')

        if value <= 0:
            raise forms.ValidationError('Jumlah harus lebih dari 0.')

        return value

    def clean_proof(self):
        f = self.cleaned_data.get('proof')
        if not f:
            raise forms.ValidationError('Berkas bukti wajib diunggah.')
        if f.size > 10 * 1024 * 1024:
            raise forms.ValidationError('Ukuran berkas maksimal 10 MB.')
        return f

# ==========================
# FORM REKAP KAS
# ==========================
class CashFlowForm(forms.ModelForm):
    class Meta:
        model = CashFlow
        fields = ['date', 'flow_type', 'amount', 'description']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'w-full rounded border px-3 py-2'}),
            'flow_type': forms.Select(attrs={'class': 'w-full rounded border px-3 py-2'}),
            'amount': forms.NumberInput(attrs={'class': 'w-full rounded border px-3 py-2', 'placeholder': 'Contoh: 150000'}),
            'description': forms.TextInput(attrs={'class': 'w-full rounded border px-3 py-2', 'placeholder': 'Keterangan transaksi'}),
        }
        labels = {
            'date': 'Tanggal',
            'flow_type': 'Tipe',
            'amount': 'Nominal (Rp)',
            'description': 'Keterangan',
        }

