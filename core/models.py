from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
import hashlib
import os

User = get_user_model()


class Mosque(models.Model):
    name = models.CharField('Nama Masjid', max_length=120)
    address = models.TextField('Alamat', blank=True)
    city = models.CharField('Kota/Kab', max_length=80, blank=True)
    province = models.CharField('Provinsi', max_length=80, blank=True)
    established_date = models.DateField('Tanggal Berdiri', null=True, blank=True)
    land_status = models.CharField('Status Tanah', max_length=120, blank=True)
    deed_number = models.CharField('No. Akta/Surat Wakaf', max_length=120, blank=True)
    npwp = models.CharField('NPWP', max_length=32, blank=True)
    bank_name = models.CharField('Bank Utama', max_length=80, blank=True)
    bank_account = models.CharField('No. Rekening', max_length=80, blank=True)
    website = models.URLField('Website', blank=True)
    logo_url = models.URLField('URL Logo', blank=True)
    about = models.TextField('Tentang Masjid', blank=True)
    contact_phone = models.CharField('Nomor Kontak (WA/Telp)', max_length=50, blank=True)
    email = models.EmailField('Email Resmi', blank=True, null=True)

    def __str__(self):
        return self.name


class DonationChannel(models.Model):
    mosque = models.ForeignKey(Mosque, on_delete=models.CASCADE, related_name='channels')
    title = models.CharField(max_length=100)
    bank = models.CharField(max_length=80, blank=True)
    account = models.CharField(max_length=80, blank=True)
    qris_image = models.ImageField(upload_to='qris/', blank=True, null=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title


class Document(models.Model):
    DOC_TYPES = [
        ('AKTA', 'Akta/Surat Wakaf'),
        ('SK',   'SK Pengurus/Organisasi'),
        ('NPWP', 'NPWP'),
        ('REK',  'Buku Rek Bank'),
        ('SOP',  'Standar Operasional Prosedur'),
        ('LAIN', 'Dokumen Lain'),
    ]
    mosque = models.ForeignKey(Mosque, on_delete=models.CASCADE, related_name='documents')
    doc_type = models.CharField(max_length=10, choices=DOC_TYPES)
    title = models.CharField(max_length=160)
    file = models.FileField(upload_to='docs/')
    is_public = models.BooleanField(default=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.get_doc_type_display()} - {self.title}"


class Management(models.Model):
    ROLE = [
        ('KET', 'Ketua DKM'),
        ('BEN', 'Bendahara'),
        ('SEK', 'Sekretaris'),
        ('IMAM', 'Imam'),
        ('LAIN', 'Lainnya'),
    ]
    mosque = models.ForeignKey(Mosque, on_delete=models.CASCADE, related_name='management')
    name = models.CharField(max_length=120)
    role = models.CharField(max_length=10, choices=ROLE)
    phone = models.CharField(max_length=50, blank=True)

    def __str__(self):
        return f"{self.name} ({self.get_role_display()})"


class Program(models.Model):
    mosque = models.ForeignKey(Mosque, on_delete=models.CASCADE, related_name='programs')
    title = models.CharField(max_length=140)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    last_update = models.DateField(null=True, blank=True)

    def __str__(self):
        return self.title


class Donor(models.Model):
    mosque = models.ForeignKey(Mosque, on_delete=models.CASCADE, related_name='donors')
    name = models.CharField(max_length=120)
    phone = models.CharField(max_length=50, blank=True)
    notes = models.TextField(blank=True)
    is_public = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class ReportFile(models.Model):
    mosque = models.ForeignKey(Mosque, on_delete=models.CASCADE, related_name='reports')
    title = models.CharField(max_length=150, default='Laporan Keuangan Masjid')
    file = models.FileField(upload_to='reports/')
    period = models.CharField(max_length=20, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    is_public = models.BooleanField(default=True)
    sha256 = models.CharField(max_length=64, editable=False, blank=True)

    sheet_map = {
        'LPK': 'Laporan Posisi Keuangan',
        'LAK': 'Laporan Aktivitas',
        'ArusKas': 'Laporan Arus Kas',
        'TB': 'Neraca Saldo',
        'BukuBesar': 'Buku Besar',
    }

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        try:
            h = hashlib.sha256()
            with open(self.file.path, 'rb') as f:
                for chunk in iter(lambda: f.read(8192), b''):
                    h.update(chunk)
            ReportFile.objects.filter(pk=self.pk).update(sha256=h.hexdigest())
            self.sha256 = h.hexdigest()
        except Exception:
            pass

    def __str__(self):
        return f"{self.title} ({self.period or self.uploaded_at:%Y-%m-%d})"


# ====== Bukti Donasi
def _proof_upload_path(instance, filename: str) -> str:
    jenis = instance.donation_type or 'OTH'
    return f"proof/{jenis}/{timezone.now():%Y/%m}/{filename}"


class DonationProof(models.Model):
    TYPE_CHOICES = [
        ('ZKT', 'Zakat'),
        ('INF', 'Infak'),
        ('SDK', 'Sedekah'),
    ]
    mosque = models.ForeignKey(Mosque, on_delete=models.CASCADE, related_name='donation_proofs')
    donation_type = models.CharField('Jenis Donasi', max_length=3, choices=TYPE_CHOICES, default='INF')
    donor_name   = models.CharField('Nama Donatur', max_length=120)
    phone        = models.CharField('No. HP/WA', max_length=50, blank=True)
    amount       = models.DecimalField('Jumlah (Rp)', max_digits=14, decimal_places=2, null=True, blank=True)
    paid_at      = models.DateField('Tanggal Transfer', null=True, blank=True)
    note         = models.TextField('Catatan', blank=True)
    proof        = models.FileField('Bukti Transfer (jpg/png/pdf)', upload_to=_proof_upload_path)
    is_public    = models.BooleanField('Tampilkan ke publik?', default=True)

    uploaded_at  = models.DateTimeField(auto_now_add=True)
    uploaded_by  = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)

    class Meta:
        ordering = ['-uploaded_at']
        indexes = [models.Index(fields=['donation_type']), models.Index(fields=['uploaded_at'])]

    def filename(self) -> str:
        try:
            return os.path.basename(self.proof.name)
        except Exception:
            return ""

    def delete(self, *args, **kwargs):
        try:
            if self.proof and self.proof.name and self.proof.storage.exists(self.proof.name):
                self.proof.storage.delete(self.proof.name)
        except Exception:
            pass
        return super().delete(*args, **kwargs)

    def __str__(self):
        return f"{self.get_donation_type_display()} - {self.donor_name} ({self.uploaded_at:%Y-%m-%d})"


class AuditLog(models.Model):
    actor = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    action = models.CharField(max_length=80)  # CREATE/UPDATE/DELETE/LOGIN/UPLOAD/EXPORT
    detail = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.action} @ {self.created_at:%Y-%m-%d %H:%M}"


class CashCategory(models.Model):
    ACTIVITY_CHOICES = [
        ('OPERASI', 'Aktivitas Operasi'),
        ('INVESTASI', 'Aktivitas Investasi'),
        ('PENDANAAN', 'Aktivitas Pendanaan'),
    ]
    FLOW_CHOICES = [
        ('IN', 'Pemasukan'),
        ('OUT', 'Pengeluaran'),
    ]
    name = models.CharField('Nama Kategori', max_length=100)
    activity_type = models.CharField('Jenis Aktivitas', max_length=15, choices=ACTIVITY_CHOICES, default='OPERASI')
    flow_type = models.CharField('Tipe Arus', max_length=5, choices=FLOW_CHOICES, default='IN')

    def __str__(self):
        return f"{self.name} ({self.get_flow_type_display()})"


class CashFlow(models.Model):
    FLOW_CHOICES = [
        ('IN', 'Pemasukan'),
        ('OUT', 'Pengeluaran'),
    ]
    mosque = models.ForeignKey(Mosque, on_delete=models.CASCADE, related_name='cashflows')
    date = models.DateField('Tanggal')
    category = models.ForeignKey(CashCategory, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Kategori Kas")
    flow_type = models.CharField('Tipe', max_length=10, choices=FLOW_CHOICES, default='IN')
    amount = models.DecimalField('Nominal (Rp)', max_digits=14, decimal_places=2)
    description = models.CharField('Keterangan', max_length=255)

    class Meta:
        ordering = ['-date']

    def save(self, *args, **kwargs):
        if self.category:
            self.flow_type = self.category.flow_type
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.get_flow_type_display()} - Rp {self.amount} ({self.date})"

