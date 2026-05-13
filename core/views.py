from pathlib import Path
import os

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import views as auth_views
from django.contrib.auth import logout
from django.http import HttpResponse, FileResponse
from django.utils.text import slugify
from django.views.decorators.clickjacking import (
    xframe_options_sameorigin,
    xframe_options_exempt,
)
from django.views.decorators.http import require_http_methods
import pandas as pd

from .models import (
    Mosque, Document, Management, Program, Donor,
    ReportFile, DonationChannel, AuditLog, DonationProof, CashFlow
)
from .forms import (
    MosqueForm, DocumentForm, ManagementForm, ProgramForm,
    DonorForm, ReportUploadForm, DonationChannelForm, DonationProofForm, CashFlowForm
)
from .excel_to_html import list_sheets, sheet_to_html, quick_summary


# -------------------------------------------------
# Util sederhana
# -------------------------------------------------
def log(request, action, detail=""):
    AuditLog.objects.create(
        actor=request.user if request.user.is_authenticated else None,
        action=action, detail=detail
    )


def ensure_mosque():
    """Pastikan ada satu record masjid agar relasi ForeignKey tidak kosong."""
    mosque = Mosque.objects.first()
    if not mosque:
        mosque = Mosque.objects.create(
            name="Masjid Al Huda",
            city="Bekasi",
            province="Jawa Barat",
        )
    return mosque


def delete_filefield(ff):
    """
    Hapus berkas pada FileField memakai Storage API (aman & portable).
    Tidak raise error jika berkas tidak ada.
    """
    try:
        if ff:
            storage = ff.storage
            name = ff.name
            if name and storage.exists(name):
                storage.delete(name)
    except Exception:
        # Jangan gagalkan flow kalau delete gagal
        pass


# -------------------------------------------------
# AUTH
# -------------------------------------------------
class LoginView(auth_views.LoginView):
    template_name = 'auth/login.html'


def do_logout(request):
    """Terima GET/POST → selalu logout & redirect (hindari 405)."""
    logout(request)
    return redirect('/')


# -------------------------------------------------
# HALAMAN PUBLIK
# -------------------------------------------------
def home(request):
    mosque = Mosque.objects.first()
    latest_report = ReportFile.objects.filter(is_public=True).order_by('-uploaded_at').first()
    channels = DonationChannel.objects.filter(is_active=True)
    docs = Document.objects.filter(is_public=True).order_by('-uploaded_at')[:10]

    # Tambahan → tampilkan pengurus & program di beranda
    pengurus = Management.objects.order_by('role', 'name')[:6]
    programs = Program.objects.filter(is_active=True).order_by('title')[:6]

    q = request.GET.get('q', '').strip()
    donors = Donor.objects.filter(is_public=True).order_by('name')
    if q:
        donors = donors.filter(name__icontains=q)

    return render(request, 'public/home.html', {
        'mosque': mosque,
        'latest_report': latest_report,
        'channels': channels,
        'docs': docs,
        'donors': donors,
        'q': q,
        'pengurus': pengurus,   # <-- baru
        'programs': programs,   # <-- baru
    })


def legalitas_public(request):
    """
    Halaman publik: menampilkan daftar dokumen legalitas (is_public=True), kecuali SOP.
    Arahkan menu ke URL name: 'legalitas_public'
    """
    mosque = Mosque.objects.first()
    # Exclude SOP agar tidak campur aduk dengan legalitas biasa
    docs = Document.objects.filter(is_public=True).exclude(doc_type='SOP').order_by('-uploaded_at')
    return render(request, 'public/legalitas.html', {
        'mosque': mosque,
        'docs': docs,
    })


def sop_public(request):
    """
    Halaman publik: menampilkan daftar dokumen SOP (is_public=True).
    """
    mosque = Mosque.objects.first()
    docs = Document.objects.filter(doc_type='SOP', is_public=True).order_by('-uploaded_at')
    return render(request, 'public/sop.html', {
        'mosque': mosque,
        'docs': docs,
    })


import json
def cashflow_public(request):
    mosque = Mosque.objects.first()
    # Mengambil data dari db
    cfs = CashFlow.objects.order_by('date')
    
    # Kelompokkan per bulan untuk grafik (YYYY-MM)
    summary = {}
    for cf in cfs:
        month_key = cf.date.strftime('%Y-%m')
        if month_key not in summary:
            summary[month_key] = {'in': 0, 'out': 0}
        
        if cf.flow_type == 'IN':
            summary[month_key]['in'] += float(cf.amount)
        else:
            summary[month_key]['out'] += float(cf.amount)
            
    labels = sorted(list(summary.keys()))
    data_in = [summary[m]['in'] for m in labels]
    data_out = [summary[m]['out'] for m in labels]
    
    context = {
        'mosque': mosque,
        'chart_labels': json.dumps(labels),
        'chart_in': json.dumps(data_in),
        'chart_out': json.dumps(data_out),
        'recent_cashflows': cfs.order_by('-date')[:10]
    }
    return render(request, 'public/rekap_kas.html', context)



def report_archive(request):
    search = request.GET.get('periode', '').strip()
    reports = ReportFile.objects.filter(is_public=True).order_by('-uploaded_at')
    if search:
        reports = reports.filter(period__icontains=search)
    return render(request, 'public/archive.html', {'reports': reports, 'search': search})


@xframe_options_sameorigin  # pastikan boleh di-embed iframe dari origin yang sama
def report_public_detail(request, pk):
    """
    Detil laporan publik:
    - Jika PDF → tampilkan viewer PDF.
    - Jika Excel → daftar sheet + quick summary.
    """
    rf = get_object_or_404(ReportFile, pk=pk, is_public=True)
    path = Path(rf.file.path)
    is_pdf = path.suffix.lower() == '.pdf'

    if is_pdf:
        return render(request, 'public/report_pdf.html', {'rf': rf})

    # Excel
    sheets = list_sheets(path)
    labeled, summary_map = [], {}
    for s in sheets:
        label = ReportFile.sheet_map.get(s, s)
        slug = slugify(s)
        labeled.append({'raw': s, 'label': label, 'slug': slug})
        try:
            ssum = quick_summary(path, s)
            if ssum:
                summary_map[slug] = ssum
        except Exception:
            pass
    return render(request, 'public/report_detail.html', {
        'rf': rf, 'sheets': labeled, 'summary_map': summary_map
    })


# === sajikan PDF inline agar tidak "refused to connect"
@xframe_options_exempt
def report_pdf_inline(request, pk):
    """
    Sajikan PDF laporan secara 'inline' agar bisa di-iframe tanpa 'refused to connect'.
    HANYA untuk file publik (is_public=True).
    """
    rf = get_object_or_404(ReportFile, pk=pk, is_public=True)
    path = Path(rf.file.path)

    if path.suffix.lower() != ".pdf":
        return HttpResponse("Not a PDF.", status=400)

    # Buka lewat FileField untuk konsistensi storage
    f = rf.file.open("rb")
    resp = FileResponse(f, content_type="application/pdf")
    resp["Content-Disposition"] = f'inline; filename="{path.name}"'
    resp["X-Frame-Options"] = "SAMEORIGIN"
    return resp


def report_public_sheet(request, pk, sheet):
    rf = get_object_or_404(ReportFile, pk=pk, is_public=True)
    path = Path(rf.file.path)
    match = None
    for s in list_sheets(path):
        if slugify(s) == sheet:
            match = s
            break
    if not match:
        messages.error(request, 'Sheet tidak ditemukan.')
        return redirect('report_public_detail', pk=pk)

    html_table = sheet_to_html(path, match)
    label = ReportFile.sheet_map.get(match, match)
    ssum = None
    try:
        ssum = quick_summary(path, match)
    except Exception:
        pass
    return render(request, 'public/report_sheet.html', {
        'rf': rf, 'sheet_label': label, 'table_html': html_table, 'sheet_raw': match, 'summary': ssum
    })


def report_public_export_csv(request, pk, sheet):
    rf = get_object_or_404(ReportFile, pk=pk, is_public=True)
    path = Path(rf.file.path)
    for s in list_sheets(path):
        if slugify(s) == sheet:
            df = pd.read_excel(path, sheet_name=s, header=0)
            resp = HttpResponse(df.to_csv(index=False), content_type='text/csv')
            resp['Content-Disposition'] = f'attachment; filename="{slugify(rf.title)}_{slugify(s)}.csv"'
            return resp
    return HttpResponse("Sheet not found", status=404)


# -------------------------------------------------
# PANEL PENGURUS (LOGIN)
# -------------------------------------------------
@login_required
def dashboard(request):
    mosque = Mosque.objects.first()
    reports = ReportFile.objects.order_by('-uploaded_at')[:10]
    docs = Document.objects.order_by('-uploaded_at')[:10]
    cashflows = CashFlow.objects.order_by('-date')[:5]
    return render(request, 'dashboard.html', {
        'mosque': mosque, 
        'reports': reports, 
        'docs': docs,
        'cashflows': cashflows
    })


@login_required
def mosque_profile(request):
    mosque = ensure_mosque()

    if request.method == 'POST':
        form = MosqueForm(request.POST, instance=mosque)
        if form.is_valid():
            form.save()
            log(request, 'UPDATE', 'Update Mosque profile')
            messages.success(request, 'Profil diperbarui.')
            return redirect('mosque_profile')
        else:
            messages.error(request, 'Form tidak valid. Mohon periksa isian.')
    else:
        form = MosqueForm(instance=mosque)

    docs = Document.objects.filter(mosque=mosque).order_by('-uploaded_at')
    mgmt = Management.objects.filter(mosque=mosque).order_by('role', 'name')
    programs = Program.objects.filter(mosque=mosque).order_by('-is_active', 'title')
    donors = Donor.objects.filter(mosque=mosque).order_by('name')
    reports = ReportFile.objects.filter(mosque=mosque).order_by('-uploaded_at')
    channels = DonationChannel.objects.filter(mosque=mosque).order_by('-is_active', 'title')

    # >>> Tambahan: preview 10 bukti donasi terakhir
    proofs = DonationProof.objects.filter(mosque=mosque).select_related('uploaded_by').order_by('-uploaded_at')[:10]
    
    cashflows = CashFlow.objects.filter(mosque=mosque).order_by('-date')

    ctx = {
        'form': form,
        'mosque': mosque,
        'docs': docs,
        'mgmt': mgmt,
        'programs': programs,
        'donors': donors,
        'reports': reports,
        'channels': channels,
        'proofs': proofs,   # <<< kirim ke template
        'cashflows': cashflows,
    }
    return render(request, 'mosque/profile.html', ctx)


    # Gunakan filter FK supaya pasti muncul meski related_name berbeda
    docs = Document.objects.filter(mosque=mosque).order_by('-uploaded_at')
    mgmt = Management.objects.filter(mosque=mosque).order_by('role', 'name')
    programs = Program.objects.filter(mosque=mosque).order_by('-is_active', 'title')
    donors = Donor.objects.filter(mosque=mosque).order_by('name')
    reports = ReportFile.objects.filter(mosque=mosque).order_by('-uploaded_at')
    channels = DonationChannel.objects.filter(mosque=mosque).order_by('-is_active', 'title')

    ctx = {
        'form': form,
        'mosque': mosque,
        'docs': docs,
        'mgmt': mgmt,
        'programs': programs,
        'donors': donors,
        'reports': reports,
        'channels': channels,
    }
    return render(request, 'mosque/profile.html', ctx)


# ----------------------------- Upload Dokumen Legalitas
@login_required
def document_upload(request):
    mosque = ensure_mosque()
    if request.method == 'POST':
        form = DocumentForm(request.POST, request.FILES)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.mosque = mosque
            obj.save()
            log(request, 'UPLOAD', f'Document {obj.title}')
            messages.success(request, 'Dokumen legalitas berhasil diunggah.')
            return redirect('mosque_profile')
        else:
            messages.error(request, 'Gagal mengunggah dokumen. Periksa isian.')
    else:
        form = DocumentForm()
    return render(request, 'docs/upload.html', {'form': form})


# === HAPUS DOKUMEN LEGALITAS (Storage API)
@login_required
@require_http_methods(["POST"])
def document_delete(request, pk):
    """
    Hapus dokumen legalitas beserta berkasnya via Storage API.
    Dipanggil via POST dari tombol Hapus (Profil/Legalitas).
    """
    d = get_object_or_404(Document, pk=pk)
    title = d.title
    delete_filefield(d.file)
    d.delete()
    log(request, "DELETE", f"Document {title}")
    messages.success(request, f"Dokumen '{title}' berhasil dihapus.")
    return redirect(request.META.get('HTTP_REFERER', 'mosque_profile'))


# ----------------------------- Master data internal
@login_required
def management_add(request):
    mosque = ensure_mosque()
    if request.method == 'POST':
        form = ManagementForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.mosque = mosque
            obj.save()
            log(request, 'CREATE', f'Management {obj.name}')
            messages.success(request, 'Pengurus ditambahkan.')
            return redirect('mosque_profile')
    else:
        form = ManagementForm()
    return render(request, 'management/form.html', {'form': form})


@login_required
def program_add(request):
    mosque = ensure_mosque()
    if request.method == 'POST':
        form = ProgramForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.mosque = mosque
            obj.save()
            log(request, 'CREATE', f'Program {obj.title}')
            messages.success(request, 'Program ditambahkan.')
            return redirect('mosque_profile')
    else:
        form = ProgramForm()
    return render(request, 'program/form.html', {'form': form})


@login_required
def donor_add(request):
    mosque = ensure_mosque()
    if request.method == 'POST':
        form = DonorForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.mosque = mosque
            obj.save()
            log(request, 'CREATE', f'Donor {obj.name}')
            messages.success(request, 'Donatur ditambahkan.')
            return redirect('mosque_profile')
    else:
        form = DonorForm()
    return render(request, 'donor/form.html', {'form': form})


@login_required
def channel_add(request):
    mosque = ensure_mosque()
    if request.method == 'POST':   # ← ini yang benar (tanpa ])
        form = DonationChannelForm(request.POST, request.FILES)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.mosque = mosque
            obj.save()
            log(request, 'CREATE', f'Channel {obj.title}')
            messages.success(request, 'Channel donasi ditambahkan.')
            return redirect('mosque_profile')
    else:
        form = DonationChannelForm()
    return render(request, 'channel/form.html', {'form': form})


@login_required
def cashflow_add(request):
    mosque = ensure_mosque()
    if request.method == 'POST':
        form = CashFlowForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.mosque = mosque
            obj.save()
            log(request, 'CREATE', f'CashFlow {obj.get_flow_type_display()} Rp{obj.amount}')
            messages.success(request, 'Data kas berhasil ditambahkan.')
            return redirect('mosque_profile')
    else:
        form = CashFlowForm()
    return render(request, 'cashflow/form.html', {'form': form, 'title': 'Catat Arus Kas'})

@login_required
def cashflow_edit(request, pk):
    obj = get_object_or_404(CashFlow, pk=pk)
    if request.method == 'POST':
        form = CashFlowForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            log(request, 'UPDATE', f'CashFlow {obj.get_flow_type_display()} Rp{obj.amount}')
            messages.success(request, 'Data kas berhasil diperbarui.')
            return redirect('mosque_profile')
    else:
        form = CashFlowForm(instance=obj)
    return render(request, 'cashflow/form.html', {'form': form, 'title': 'Edit Arus Kas'})





# ---------- HAPUS PENGURUS & PROGRAM (BARU DITAMBAHKAN)
@login_required
@require_http_methods(["POST"])
def management_delete(request, pk):
    obj = get_object_or_404(Management, pk=pk)
    name = obj.name
    obj.delete()
    log(request, "DELETE", f"Management {name}")
    messages.success(request, f"Pengurus '{name}' dihapus.")
    return redirect("mosque_profile")


@login_required
@require_http_methods(["POST"])
def program_delete(request, pk):
    obj = get_object_or_404(Program, pk=pk)
    title = obj.title
    obj.delete()
    log(request, "DELETE", f"Program {title}")
    messages.success(request, f"Program '{title}' dihapus.")
    return redirect("mosque_profile")

@login_required
@require_http_methods(["POST"])
def cashflow_delete(request, pk):
    obj = get_object_or_404(CashFlow, pk=pk)
    desc = obj.description
    obj.delete()
    log(request, "DELETE", f"CashFlow {desc}")
    messages.success(request, f"Data kas '{desc}' dihapus.")
    return redirect("mosque_profile")
# ---------- /HAPUS PENGURUS & PROGRAM & KAS


# ----------------------------- Laporan
@login_required
def report_upload(request):
    mosque = ensure_mosque()
    if request.method == 'POST':
        form = ReportUploadForm(request.POST, request.FILES)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.mosque = mosque
            obj.save()
            log(request, 'UPLOAD', f'Report {obj.title} (SHA256 {obj.sha256[:10]}...)')
            messages.success(request, 'Laporan keuangan berhasil diunggah.')
            return redirect('mosque_profile')
        else:
            messages.error(request, 'Gagal mengunggah laporan. Periksa isian.')
    else:
        form = ReportUploadForm()
    return render(request, 'reports/upload.html', {'form': form})


@login_required
@xframe_options_sameorigin  # agar PDF di detail panel juga boleh di-embed
def report_detail(request, pk):
    rf = get_object_or_404(ReportFile, pk=pk)
    path = Path(rf.file.path)
    is_pdf = path.suffix.lower() == '.pdf'

    if is_pdf:
        return render(request, 'reports/detail_pdf.html', {'rf': rf})

    # Excel
    sheets = list_sheets(path)
    labeled, summary_map = [], {}
    for s in sheets:
        slug = slugify(s)
        labeled.append({'raw': s, 'label': ReportFile.sheet_map.get(s, s), 'slug': slug})
        try:
            ssum = quick_summary(path, s)
            if ssum:
                summary_map[slug] = ssum
        except Exception:
            pass
    return render(request, 'reports/detail.html', {'rf': rf, 'sheets': labeled, 'summary_map': summary_map})


@login_required
def report_sheet(request, pk, sheet):
    rf = get_object_or_404(ReportFile, pk=pk)
    path = Path(rf.file.path)
    match = None
    for s in list_sheets(path):
        if slugify(s) == sheet:
            match = s
            break
    if not match:
        messages.error(request, 'Sheet tidak ditemukan.')
        return redirect('report_detail', pk=pk)

    table_html = sheet_to_html(path, match)
    label = ReportFile.sheet_map.get(match, match)
    ssum = None
    try:
        ssum = quick_summary(path, match)
    except Exception:
        pass
    return render(request, 'reports/sheet.html', {
        'rf': rf, 'sheet_label': label, 'table_html': table_html, 'summary': ssum
    })


@login_required
def report_export_csv(request, pk, sheet):
    path = Path(get_object_or_404(ReportFile, pk=pk).file.path)
    for s in list_sheets(path):
        if slugify(s) == sheet:
            df = pd.read_excel(path, sheet_name=s, header=0)
            log(request, 'EXPORT', f'CSV {s}')
            resp = HttpResponse(df.to_csv(index=False), content_type='text/csv')
            resp['Content-Disposition'] = f'attachment; filename="laporan_{slugify(s)}.csv"'
            return resp
    return HttpResponse("Sheet not found", status=404)


# === HAPUS LAPORAN KEUANGAN (dari Profil/Panel) → kembali ke profil
@login_required
@require_http_methods(["POST"])
def report_delete(request, pk):
    rf = get_object_or_404(ReportFile, pk=pk)
    title = rf.title
    delete_filefield(rf.file)
    rf.delete()
    log(request, "DELETE", f"Report {title}")
    messages.success(request, f"Laporan '{title}' berhasil dihapus.")
    return redirect("mosque_profile")


# === HAPUS LAPORAN KEUANGAN dari HALAMAN ARSIP → kembali ke arsip
@login_required
@require_http_methods(["POST"])
def report_delete_from_archive(request, pk):
    rf = get_object_or_404(ReportFile, pk=pk)
    title = rf.title
    delete_filefield(rf.file)
    rf.delete()
    log(request, "DELETE", f"Report {title} (from archive)")
    messages.success(request, f"Laporan '{title}' berhasil dihapus.")
    return redirect("report_archive")


# -------------------------------------------------
# HALAMAN DONASI (Zakat, Infaq, Sedekah) + Upload Bukti
# -------------------------------------------------
def donation_page(request):
    """Halaman publik: pilih jenis donasi dan/atau unggah bukti transfer."""
    mosque = Mosque.objects.first()

    zakat_url   = "https://docs.google.com/spreadsheets/d/1sWExzhxIwx3Yv4aowGmoQgKQEtO1Va-qAx5w2d_bOCI/edit?gid=0#gid=0"
    infaq_url   = "https://docs.google.com/spreadsheets/d/1Jr7eMjkGvjz2_pMermi2dTpf0i5yPdQIRTfNkyJZ6Rg/edit?gid=0#gid=0"
    sedekah_url = "https://docs.google.com/spreadsheets/d/1GTRhI_qnL-7WYb1BjOCf7_w-xyNAsDar1sVmqGan57Q/edit?gid=0#gid=0"
    return render(request, "public/donasi.html", {
        'mosque': mosque,
        'zakat_url': zakat_url,
        'infaq_url': infaq_url,
        'sedekah_url': sedekah_url,
    })


# helper untuk label
_DTYPE_LABEL = {'ZKT': 'Zakat', 'INF': 'Infak', 'SDK': 'Sedekah'}

def _normalize_dtype(dtype: str) -> str:
    d = (dtype or '').upper()
    if d.startswith('Z'): return 'ZKT'
    if d.startswith('I'): return 'INF'
    if d.startswith('S'): return 'SDK'
    return 'INF'


# -------- DONASI: upload bukti publik
def donation_proof_upload(request, dtype: str):
    mosque = ensure_mosque()
    code = _normalize_dtype(dtype)
    label = _DTYPE_LABEL.get(code, 'Infak')

    if request.method == 'POST':
        form = DonationProofForm(request.POST, request.FILES)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.mosque = mosque
            obj.donation_type = code
            if request.user.is_authenticated:
                obj.uploaded_by = request.user
            obj.save()
            log(request, 'UPLOAD', f'DonationProof {label} - {obj.donor_name}')
            messages.success(request, "Bukti transfer berhasil diunggah. Terima kasih.")
            return redirect('donation_page')
        messages.error(request, "Gagal mengunggah. Periksa isian.")
    else:
        form = DonationProofForm(initial={'donation_type': code})

    return render(request, "public/donasi_upload.html", {'form': form, 'dtype': code, 'label': label})


# -------- DONASI: admin list & delete (login)
@login_required
def donation_proof_admin(request):
    proofs = DonationProof.objects.select_related('uploaded_by').order_by('-uploaded_at')
    q = request.GET.get('q', '').strip()
    if q:
        proofs = proofs.filter(donor_name__icontains=q)
    return render(request, "donasi/admin_list.html", {'proofs': proofs})

@login_required
@require_http_methods(["POST"])
def donation_proof_delete(request, pk: int):
    obj = get_object_or_404(DonationProof, pk=pk)
    name = obj.donor_name
    obj.delete()
    log(request, 'DELETE', f'DonationProof {name}')
    messages.success(request, f"Bukti donasi '{name}' dihapus.")
    return redirect('donation_proof_admin')
