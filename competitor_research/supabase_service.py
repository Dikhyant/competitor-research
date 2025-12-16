"""
Supabase service utility for competitor research project.

This module provides a convenient interface for interacting with Supabase.
"""

from django.conf import settings
from supabase import create_client, Client
import logging

logger = logging.getLogger(__name__)


class SupabaseService:
    """Service class for Supabase interactions."""
    
    def __init__(self):
        """Initialize the Supabase client with URL and key from settings."""
        self.url = settings.SUPABASE_URL
        self.key = settings.SUPABASE_KEY
        
        if not self.url:
            raise ValueError("SUPABASE_URL is not set in Django settings")
        if not self.key:
            raise ValueError("SUPABASE_KEY is not set in Django settings")
        
        self.client: Client = create_client(self.url, self.key)
    
    def get_client(self) -> Client:
        """
        Get the Supabase client instance.
        
        Returns:
            The Supabase client object
        """
        return self.client
    
    # Company methods
    def get_companies(self, limit=100):
        """
        Get all companies from the database.
        
        Args:
            limit: Maximum number of records to return (default: 100)
        
        Returns:
            List of company records
        """
        try:
            response = self.client.table('companies').select('*').limit(limit).execute()
            return response.data
        except Exception as e:
            logger.error(f"Error fetching companies: {str(e)}")
            raise
    
    def get_company(self, company_id):
        """
        Get a single company by ID.
        
        Args:
            company_id: UUID of the company
        
        Returns:
            Company record or None
        """
        try:
            response = self.client.table('companies').select('*').eq('id', company_id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error fetching company {company_id}: {str(e)}")
            raise
    
    def create_company(self, name, website_url=None):
        """
        Create a new company.
        
        Args:
            name: Company name
            website_url: Optional website URL
        
        Returns:
            Created company record
        """
        try:
            data = {'name': name}
            if website_url:
                data['website_url'] = website_url
            
            response = self.client.table('companies').insert(data).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error creating company: {str(e)}")
            raise
    
    def update_company(self, company_id, **kwargs):
        """
        Update a company.
        
        Args:
            company_id: UUID of the company
            **kwargs: Fields to update (name, website_url, etc.)
        
        Returns:
            Updated company record
        """
        try:
            response = self.client.table('companies').update(kwargs).eq('id', company_id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error updating company {company_id}: {str(e)}")
            raise
    
    def delete_company(self, company_id):
        """
        Delete a company.
        
        Args:
            company_id: UUID of the company
        
        Returns:
            True if successful
        """
        try:
            self.client.table('companies').delete().eq('id', company_id).execute()
            return True
        except Exception as e:
            logger.error(f"Error deleting company {company_id}: {str(e)}")
            raise
    
    # Company Funding methods
    def get_company_funding(self, company_id=None, limit=100):
        """
        Get company funding records.
        
        Args:
            company_id: Optional company ID to filter by
            limit: Maximum number of records to return
        
        Returns:
            List of funding records
        """
        try:
            query = self.client.table('company_funding').select('*')
            if company_id:
                query = query.eq('company_id', company_id)
            response = query.limit(limit).execute()
            return response.data
        except Exception as e:
            logger.error(f"Error fetching company funding: {str(e)}")
            raise
    
    def create_company_funding(self, company_id, value_usd, year, source_url):
        """
        Create a company funding record.
        
        Args:
            company_id: UUID of the company
            value_usd: Funding value in USD
            year: Year of funding
            source_url: Source URL for the funding information
        
        Returns:
            Created funding record
        """
        try:
            data = {
                'company_id': company_id,
                'value_usd': float(value_usd),
                'year': year,
                'source_url': source_url
            }
            response = self.client.table('company_funding').insert(data).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error creating company funding: {str(e)}")
            raise
    
    # Company Networth methods
    def get_company_networth(self, company_id=None, limit=100):
        """
        Get company networth records.
        
        Args:
            company_id: Optional company ID to filter by
            limit: Maximum number of records to return
        
        Returns:
            List of networth records
        """
        try:
            query = self.client.table('company_networth').select('*')
            if company_id:
                query = query.eq('company_id', company_id)
            response = query.limit(limit).execute()
            return response.data
        except Exception as e:
            logger.error(f"Error fetching company networth: {str(e)}")
            raise
    
    def create_company_networth(self, company_id, value_usd, year, source_url):
        """
        Create a company networth record.
        
        Args:
            company_id: UUID of the company
            value_usd: Networth value in USD
            year: Year of networth
            source_url: Source URL for the networth information
        
        Returns:
            Created networth record
        """
        try:
            data = {
                'company_id': company_id,
                'value_usd': float(value_usd),
                'year': year,
                'source_url': source_url
            }
            response = self.client.table('company_networth').insert(data).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error creating company networth: {str(e)}")
            raise
    
    # Company Users methods
    def get_company_users(self, company_id=None, limit=100):
        """
        Get company user count records.
        
        Args:
            company_id: Optional company ID to filter by
            limit: Maximum number of records to return
        
        Returns:
            List of user count records
        """
        try:
            query = self.client.table('company_users').select('*')
            if company_id:
                query = query.eq('company_id', company_id)
            response = query.limit(limit).execute()
            return response.data
        except Exception as e:
            logger.error(f"Error fetching company users: {str(e)}")
            raise
    
    def create_company_users(self, company_id, value, year, source_url):
        """
        Create a company user count record.
        
        Args:
            company_id: UUID of the company
            value: Number of users
            year: Year of user count
            source_url: Source URL for the user count information
        
        Returns:
            Created user count record
        """
        try:
            data = {
                'company_id': company_id,
                'value': int(value),
                'year': year,
                'source_url': source_url
            }
            response = self.client.table('company_users').insert(data).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error creating company users: {str(e)}")
            raise


# Convenience function to get a service instance
def get_supabase_service():
    """Get an instance of SupabaseService."""
    return SupabaseService()

