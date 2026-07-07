from django.test import TestCase, Client
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from core.models import Mosque, Document, CashCategory
from core.views import ensure_categories

User = get_user_model()

class SOPTestCase(TestCase):
    def setUp(self):
        # Buat masjid
        self.mosque = Mosque.objects.create(
            name="Masjid Al Huda",
            city="Bekasi",
            province="Jawa Barat"
        )
        # Buat user admin
        self.user = User.objects.create_superuser(
            username="admin",
            password="adminpassword",
            email="admin@test.com"
        )
        self.client = Client()

    def test_sop_public_empty(self):
        # Test halaman publik tanpa SOP
        response = self.client.get(reverse('sop_public'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Belum ada dokumen SOP")

    def test_sop_public_with_multiple_docs(self):
        # Buat dummy file PDF
        dummy_pdf = SimpleUploadedFile("sop1.pdf", b"dummy content", content_type="application/pdf")
        dummy_pdf_2 = SimpleUploadedFile("sop2.pdf", b"dummy content", content_type="application/pdf")
        
        # Simpan SOP 1
        sop1 = Document.objects.create(
            mosque=self.mosque,
            doc_type='SOP',
            title='SOP Penerimaan Kas Tunai',
            file=dummy_pdf,
            is_public=True
        )
        
        # Simpan SOP 2
        sop2 = Document.objects.create(
            mosque=self.mosque,
            doc_type='SOP',
            title='SOP Pengeluaran Kas Tunai',
            file=dummy_pdf_2,
            is_public=True
        )

        # Cek halaman publik
        response = self.client.get(reverse('sop_public'))
        self.assertEqual(response.status_code, 200)
        
        # Cek apakah judul SOP1 dan SOP2 ada di daftar
        self.assertContains(response, 'SOP Penerimaan Kas Tunai')
        self.assertContains(response, 'SOP Pengeluaran Kas Tunai')
        
        # Secara default, SOP terbaru (SOP2) harus aktif
        self.assertEqual(response.context['sop_doc'].pk, sop2.pk)

        # Cek halaman publik dengan query param ?id=
        response = self.client.get(reverse('sop_public') + f'?id={sop1.pk}')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['sop_doc'].pk, sop1.pk)

    def test_sop_upload_keeps_old_sops(self):
        # Login admin
        self.client.login(username="admin", password="adminpassword")
        
        # Upload SOP pertama
        dummy_pdf = SimpleUploadedFile("sop1.pdf", b"dummy content", content_type="application/pdf")
        response = self.client.post(reverse('sop_upload'), {
            'title': 'SOP Pertama',
            'file': dummy_pdf,
            'is_public': True
        })
        self.assertEqual(response.status_code, 302) # Redirect to /dashboard/?tab=dokumen
        
        # Upload SOP kedua
        dummy_pdf_2 = SimpleUploadedFile("sop2.pdf", b"dummy content 2", content_type="application/pdf")
        response = self.client.post(reverse('sop_upload'), {
            'title': 'SOP Kedua',
            'file': dummy_pdf_2,
            'is_public': True
        })
        self.assertEqual(response.status_code, 302)

        # Pastikan kedua SOP masih ada di database
        sops = Document.objects.filter(mosque=self.mosque, doc_type='SOP')
        self.assertEqual(sops.count(), 2)
        self.assertTrue(sops.filter(title='SOP Pertama').exists())
        self.assertTrue(sops.filter(title='SOP Kedua').exists())


class CashCategoryTestCase(TestCase):
    def setUp(self):
        self.mosque = Mosque.objects.create(
            name="Masjid Al Huda",
            city="Bekasi",
            province="Jawa Barat"
        )

    def test_ensure_categories_sets_codes(self):
        ensure_categories()
        # Verifikasi bahwa kategori terbuat dengan kode akun yang benar
        cat = CashCategory.objects.filter(name='Kotak Amal / Infak / Sedekah').first()
        self.assertIsNotNone(cat)
        self.assertEqual(cat.code, '4101')

    def test_category_string_representation(self):
        cat_with_code = CashCategory.objects.create(
            name='Test Kategori Berkode',
            code='9999',
            activity_type='OPERASI',
            flow_type='IN'
        )
        cat_without_code = CashCategory.objects.create(
            name='Test Kategori Tanpa Kode',
            activity_type='OPERASI',
            flow_type='IN'
        )
        self.assertEqual(str(cat_with_code), '[9999] Test Kategori Berkode (Pemasukan)')
        self.assertEqual(str(cat_without_code), 'Test Kategori Tanpa Kode (Pemasukan)')

