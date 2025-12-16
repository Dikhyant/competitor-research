from django.contrib import admin
from .models import Company, CompanyFunding, CompanyNetworth, CompanyUsers


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ['name', 'website_url', 'created_at', 'updated_at']
    search_fields = ['name', 'website_url']
    list_filter = ['created_at', 'updated_at']


@admin.register(CompanyFunding)
class CompanyFundingAdmin(admin.ModelAdmin):
    list_display = ['company', 'value_usd', 'year', 'created_at']
    list_filter = ['year', 'created_at']
    search_fields = ['company__name', 'source_url']
    raw_id_fields = ['company']


@admin.register(CompanyNetworth)
class CompanyNetworthAdmin(admin.ModelAdmin):
    list_display = ['company', 'value_usd', 'year', 'created_at']
    list_filter = ['year', 'created_at']
    search_fields = ['company__name', 'source_url']
    raw_id_fields = ['company']


@admin.register(CompanyUsers)
class CompanyUsersAdmin(admin.ModelAdmin):
    list_display = ['company', 'value', 'year', 'created_at']
    list_filter = ['year', 'created_at']
    search_fields = ['company__name', 'source_url']
    raw_id_fields = ['company']
