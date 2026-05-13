from django.contrib import admin
from .models import (Mosque, DonationChannel, Document, Management,
                     Program, Donor, ReportFile, AuditLog)

admin.site.register(Mosque)
admin.site.register(DonationChannel)
admin.site.register(Document)
admin.site.register(Management)
admin.site.register(Program)
admin.site.register(Donor)
admin.site.register(ReportFile)
admin.site.register(AuditLog)
