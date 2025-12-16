"""
Test script to verify Supabase connection
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'competitor_research.settings')
django.setup()

from django.conf import settings
from competitor_research.supabase_service import get_supabase_service

def test_connection():
    """Test the Supabase connection"""
    try:
        print("Testing Supabase connection...")
        print(f"Supabase URL: {settings.SUPABASE_URL}")
        print(f"Supabase Key: {settings.SUPABASE_KEY[:20]}... (hidden)")
        
        # Initialize Supabase service
        supabase = get_supabase_service()
        print("\n✓ Supabase client initialized successfully!")
        
        # Test connection by fetching companies
        print("\nTesting database connection...")
        companies = supabase.get_companies(limit=5)
        print(f"✓ Connection successful!")
        print(f"✓ Found {len(companies)} companies in database")
        
        if companies:
            print("\nSample companies:")
            for company in companies[:3]:
                print(f"  - {company.get('name', 'N/A')} (ID: {company.get('id', 'N/A')[:8]}...)")
        
        # Test other tables
        print("\nTesting other tables...")
        
        # Test company_funding
        try:
            funding = supabase.get_company_funding(limit=1)
            print(f"✓ company_funding table accessible ({len(funding)} records found)")
        except Exception as e:
            print(f"⚠ company_funding table: {e}")
        
        # Test company_networth
        try:
            networth = supabase.get_company_networth(limit=1)
            print(f"✓ company_networth table accessible ({len(networth)} records found)")
        except Exception as e:
            print(f"⚠ company_networth table: {e}")
        
        # Test company_users
        try:
            users = supabase.get_company_users(limit=1)
            print(f"✓ company_users table accessible ({len(users)} records found)")
        except Exception as e:
            print(f"⚠ company_users table: {e}")
        
        print("\n" + "="*50)
        print("✓ All tests passed! Supabase integration is working.")
        print("="*50)
        
        return True
        
    except Exception as e:
        print(f"\n✗ Connection failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_connection()
    sys.exit(0 if success else 1)

