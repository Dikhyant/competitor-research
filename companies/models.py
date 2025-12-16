import uuid
from django.db import models
from django.utils import timezone


class Company(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.TextField()
    website_url = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'companies'
        ordering = ['-created_at']

    def __str__(self):
        return self.name


class CompanyFunding(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='funding_records')
    value_usd = models.DecimalField(max_digits=20, decimal_places=2)
    year = models.IntegerField()
    source_url = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'company_funding'
        ordering = ['-year', '-created_at']

    def __str__(self):
        return f"{self.company.name} - ${self.value_usd} ({self.year})"


class CompanyNetworth(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='networth_records')
    value_usd = models.DecimalField(max_digits=20, decimal_places=2)
    year = models.IntegerField()
    source_url = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'company_networth'
        ordering = ['-year', '-created_at']

    def __str__(self):
        return f"{self.company.name} - ${self.value_usd} ({self.year})"


class CompanyUsers(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='user_records')
    value = models.BigIntegerField()
    year = models.IntegerField()
    source_url = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'company_users'
        ordering = ['-year', '-created_at']
        verbose_name = 'Company Users'
        verbose_name_plural = 'Company Users'

    def __str__(self):
        return f"{self.company.name} - {self.value} users ({self.year})"
