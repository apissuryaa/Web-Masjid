from django.contrib import admin
from .models import (Mosque, DonationChannel, Document, Management,
                     Program, Donor, ReportFile, AuditLog, CashCategory, CashFlow)

admin.site.register(Mosque)
admin.site.register(DonationChannel)
admin.site.register(Document)
admin.site.register(Management)
admin.site.register(Program)
admin.site.register(Donor)
admin.site.register(ReportFile)
admin.site.register(AuditLog)

@admin.register(CashCategory)
class CashCategoryAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'activity_type', 'flow_type')
    list_filter = ('activity_type', 'flow_type')
    search_fields = ('code', 'name')
    ordering = ('code', 'name')

@admin.register(CashFlow)
class CashFlowAdmin(admin.ModelAdmin):
    list_display = ('date', 'category', 'flow_type', 'amount', 'description')
    list_filter = ('flow_type', 'category')
    search_fields = ('description', 'category__name')
    ordering = ('-date',)
