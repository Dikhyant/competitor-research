import json
import logging
from django.http import JsonResponse, StreamingHttpResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from competitor_research.openai_service import get_openai_service
from competitor_research.supabase_service import get_supabase_service

logger = logging.getLogger(__name__)


def home(request):
    """Render the home page with URL input form."""
    return render(request, 'companies/home.html')


@csrf_exempt
@require_http_methods(["GET", "POST"])
def find_competitors(request):
    """
    API endpoint to find competitors for a given company URL.
    Uses Server-Sent Events (SSE) to stream progressive updates.
    
    Accepts:
    - GET: ?url=<company_url> (for EventSource/SSE)
    - POST: {"url": "<company_url>"} (for regular requests, returns streaming)
    
    Returns: Streaming response with SSE events
    """
    try:
        # Get company URL from request
        if request.method == "POST":
            try:
                data = json.loads(request.body)
                company_url = data.get("url")
            except json.JSONDecodeError:
                return JsonResponse(
                    {"error": "Invalid JSON in request body"},
                    status=400
                )
        else:  # GET
            company_url = request.GET.get("url")
        
        if not company_url:
            return JsonResponse(
                {"error": "Company URL is required. Use 'url' parameter."},
                status=400
            )
        
        # Return streaming response
        response = StreamingHttpResponse(
            stream_competitors_research(company_url),
            content_type='text/event-stream'
        )
        response['Cache-Control'] = 'no-cache'
        response['X-Accel-Buffering'] = 'no'
        response['Access-Control-Allow-Origin'] = '*'
        return response
        
    except Exception as e:
        logger.error(f"Error finding competitors: {str(e)}", exc_info=True)
        return JsonResponse(
            {"error": f"An error occurred: {str(e)}"},
            status=500
        )


def find_and_save_competitors(company_url, main_company_id, supabase_service, openai_service):
    """
    Helper function to find competitors using OpenAI and save them to the database.
    Also saves/updates the main company and sets its competitor_ids.
    
    Args:
        company_url: URL of the main company
        main_company_id: ID of the main company if it exists, None otherwise
        supabase_service: SupabaseService instance
        openai_service: OpenAIService instance
    
    Yields:
        SSE events for competitors found and saved
    """
    # Build the prompt to find competitors
    prompt = """You are a business analyst with 20 years of experience. You can take any company's website url, and do research about it and figure out who their competitors are.

IMPORTANT: You must respond with ONLY a valid JSON array. Do not include any explanatory text, markdown formatting, or code blocks. Return only the raw JSON array.

The output must be a JSON array where each object has this exact structure:
{
  "name": "<company name>",
  "url": "<company website URL>"
}

Company URL: """ + company_url + """

Remember: Output ONLY the JSON array, nothing else."""

    # Call OpenAI service
    response_text = openai_service.get_text_completion(
        prompt,
        model="gpt-4",  # Using GPT-4 for better analysis
        temperature=0.7
    )
    
    # Parse the response to extract JSON array
    competitors = parse_competitors_response(response_text)
    
    # Send competitors list event
    yield f"data: {json.dumps({'type': 'competitors_list', 'total': len(competitors)})}\n\n"
    
    # Ensure main company exists in database
    if not main_company_id:
        # Try to find by URL first
        existing_main = supabase_service.get_company_by_url(company_url)
        if existing_main:
            main_company_id = existing_main['id']
        else:
            # Create main company (extract name from URL or use URL as name)
            import re
            from urllib.parse import urlparse
            parsed_url = urlparse(company_url)
            domain = parsed_url.netloc.replace('www.', '')
            company_name = domain.split('.')[0].capitalize() if domain else company_url
            
            new_main_company = supabase_service.create_company(
                name=company_name,
                website_url=company_url
            )
            if new_main_company:
                main_company_id = new_main_company['id']
                logger.info(f"Created main company: {company_name}")
            else:
                logger.error("Failed to create main company")
                main_company_id = None
    
    # Save competitors to Supabase database
    saved_competitors = []
    competitor_ids = []
    
    for competitor in competitors:
        try:
            competitor_name = competitor.get("name", "").strip()
            competitor_url = competitor.get("url", "").strip()
            
            if not competitor_name:
                logger.warning(f"Skipping competitor with missing name: {competitor}")
                continue
            
            # Check if company already exists by URL (if available) or by name
            existing_company = None
            
            if competitor_url:
                # Try to find by URL first (most reliable)
                try:
                    existing_company = supabase_service.get_company_by_url(competitor_url)
                except Exception as e:
                    logger.warning(f"Error checking for existing company by URL: {str(e)}")
            
            # If not found by URL, try to find by name
            if not existing_company:
                try:
                    response = supabase_service.client.table('companies').select('*').eq('name', competitor_name).limit(1).execute()
                    if response.data:
                        existing_company = response.data[0]
                except Exception as e:
                    logger.warning(f"Error checking for existing company by name: {str(e)}")
            
            if existing_company:
                # Company exists, update if needed
                company_id = existing_company['id']
                update_data = {}
                
                if existing_company.get('name') != competitor_name:
                    update_data['name'] = competitor_name
                
                if competitor_url and existing_company.get('website_url') != competitor_url:
                    update_data['website_url'] = competitor_url
                
                if update_data:
                    try:
                        updated = supabase_service.update_company(company_id, **update_data)
                        existing_company = updated if updated else existing_company
                    except Exception as e:
                        logger.warning(f"Error updating company: {str(e)}")
                
                saved_competitor = {
                    "id": existing_company['id'],
                    "name": existing_company.get('name', competitor_name),
                    "url": existing_company.get('website_url', competitor_url) or "",
                    "created": False  # Existing record
                }
                saved_competitors.append(saved_competitor)
                competitor_ids.append(company_id)
                logger.info(f"Found existing company: {existing_company.get('name', competitor_name)}")
            else:
                # Create new company
                new_company = supabase_service.create_company(
                    name=competitor_name,
                    website_url=competitor_url if competitor_url else None
                )
                
                if new_company:
                    saved_competitor = {
                        "id": new_company['id'],
                        "name": new_company.get('name', competitor_name),
                        "url": new_company.get('website_url', competitor_url) or "",
                        "created": True  # New record
                    }
                    saved_competitors.append(saved_competitor)
                    competitor_ids.append(new_company['id'])
                    logger.info(f"Created new company: {competitor_name}")
                else:
                    raise Exception("Failed to create company - no data returned")
            
            # Send individual competitor event
            yield f"data: {json.dumps({'type': 'competitor', 'competitor': saved_competitor})}\n\n"
                    
        except Exception as e:
            logger.error(f"Error saving competitor {competitor.get('name')}: {str(e)}")
            # Still include in response even if save failed
            error_competitor = {
                "name": competitor.get("name", ""),
                "url": competitor.get("url", ""),
                "error": f"Failed to save: {str(e)}"
            }
            saved_competitors.append(error_competitor)
            yield f"data: {json.dumps({'type': 'competitor', 'competitor': error_competitor})}\n\n"
    
    # Update main company's competitor_ids
    if main_company_id and competitor_ids:
        try:
            supabase_service.update_company_competitor_ids(main_company_id, competitor_ids)
            logger.info(f"Updated competitor_ids for main company: {len(competitor_ids)} competitors")
        except Exception as e:
            logger.error(f"Error updating competitor_ids for main company: {str(e)}")
    
    return saved_competitors


def stream_competitors_research(company_url):
    """
    Generator function that yields SSE events as competitors are found and researched.
    """
    try:
        # Send initial status
        yield f"data: {json.dumps({'type': 'status', 'message': 'Checking database for existing company...'})}\n\n"
        
        # Initialize services
        supabase_service = get_supabase_service()
        openai_service = get_openai_service()
        
        # Check if company exists in database by URL
        existing_company = supabase_service.get_company_by_url(company_url)
        saved_competitors = []
        
        if existing_company:
            # Company exists, check for competitors
            competitor_ids = existing_company.get('competitor_ids', [])
            
            if competitor_ids and len(competitor_ids) > 0:
                # Competitors exist, fetch them from database
                yield f"data: {json.dumps({'type': 'status', 'message': f'Found existing company with {len(competitor_ids)} competitors in database...'})}\n\n"
                
                competitors_list = supabase_service.get_competitors_by_ids(competitor_ids)
                
                # Convert to the format expected by the rest of the code
                for comp in competitors_list:
                    saved_competitor = {
                        "id": comp['id'],
                        "name": comp.get('name', ''),
                        "url": comp.get('website_url', '') or "",
                        "created": False  # Existing record
                    }
                    saved_competitors.append(saved_competitor)
                
                # Send competitors list event
                yield f"data: {json.dumps({'type': 'competitors_list', 'total': len(saved_competitors)})}\n\n"
                
                # Send individual competitor events
                for saved_competitor in saved_competitors:
                    yield f"data: {json.dumps({'type': 'competitor', 'competitor': saved_competitor})}\n\n"
            else:
                # Company exists but no competitors, need to find them
                yield f"data: {json.dumps({'type': 'status', 'message': 'Company found but no competitors. Finding competitors...'})}\n\n"
                saved_competitors = yield from find_and_save_competitors(
                    company_url, existing_company['id'], supabase_service, openai_service
                )
        else:
            # Company doesn't exist, need to find competitors
            yield f"data: {json.dumps({'type': 'status', 'message': 'Company not found. Finding competitors...'})}\n\n"
            saved_competitors = yield from find_and_save_competitors(
                company_url, None, supabase_service, openai_service
            )
        
        # Send status that we're starting research
        yield f"data: {json.dumps({'type': 'status', 'message': 'Starting competitor research...', 'total_competitors': len(saved_competitors)})}\n\n"
        
        # Research each competitor URL for networth, users, and funding data
        research_results = []
        total_competitors = len([c for c in saved_competitors if "error" not in c and c.get("url")])
        researched_count = 0
        
        for competitor in saved_competitors:
            if "error" in competitor or not competitor.get("url"):
                continue
            
            competitor_url = competitor.get("url")
            competitor_id = competitor.get("id")
            
            try:
                # Send status that we're checking/researching this competitor
                yield f"data: {json.dumps({'type': 'research_status', 'competitor_id': competitor_id, 'competitor_name': competitor.get('name'), 'status': 'checking'})}\n\n"
                
                # Check if analysis already exists in Supabase
                existing_analysis = supabase_service.get_company_analysis(competitor_id)
                
                if existing_analysis:
                    # Analysis exists, stream it directly
                    logger.info(f"Found existing analysis for {competitor.get('name')}, streaming from database")
                    yield f"data: {json.dumps({'type': 'research_status', 'competitor_id': competitor_id, 'competitor_name': competitor.get('name'), 'status': 'found_in_db'})}\n\n"
                    
                    research_result = {
                        "competitor_id": competitor_id,
                        "competitor_name": competitor.get("name"),
                        "status": "success",
                        "from_cache": True,  # Indicate this came from database
                        "networth_count": len(existing_analysis.get("networth", [])),
                        "users_count": len(existing_analysis.get("users", [])),
                        "funding_count": len(existing_analysis.get("funding", [])),
                        # Include actual data for graphs
                        "networth": existing_analysis.get("networth", []),
                        "users": existing_analysis.get("users", []),
                        "funding": existing_analysis.get("funding", [])
                    }
                    research_results.append(research_result)
                    researched_count += 1
                    
                    # Send research complete event for this competitor
                    yield f"data: {json.dumps({'type': 'competitor_research', 'result': research_result})}\n\n"
                else:
                    # No existing analysis, use OpenAI
                    logger.info(f"No existing analysis for {competitor.get('name')}, using OpenAI")
                    yield f"data: {json.dumps({'type': 'research_status', 'competitor_id': competitor_id, 'competitor_name': competitor.get('name'), 'status': 'analyzing'})}\n\n"
                    
                    # Build the research prompt
                    research_prompt = """You are a business analyst with 20 years of experience. You can take any company's website url, and do research about it and figure out how their networth has changed since they have started their company, how their number of users have changed since they started the business and how much funding they have made since the start of their company.

IMPORTANT: You must respond with ONLY valid JSON. Do not include any explanatory text, markdown formatting, or code blocks. Return only the raw JSON object.

The output must be a JSON object with this exact structure:

{
  "networth": [],
  "users": [],
  "funding": []
}

The "networth" array contains objects with this structure (each object must have these exact keys):
{
  "value": 1234567.89,
  "year": 2023,
  "source": "https://example.com/source"
}
Note: "value" must be a number in USD (normalize currency to USD if needed), "year" must be a number, "source" must be a valid URL string.

The "users" array contains objects with this structure (each object must have these exact keys):
{
  "value": 1000000,
  "year": 2023,
  "source": "https://example.com/source"
}
Note: "value" must be a number representing total users, "year" must be a number, "source" must be a valid URL string.

The "funding" array contains objects with this structure (each object must have these exact keys):
{
  "value": 5000000.00,
  "year": 2023,
  "source": "https://example.com/source"
}
Note: "value" must be a number in USD representing funding amount, "year" must be a number, "source" must be a valid URL string.

Company URL: """ + competitor_url + """

Remember: Output ONLY the JSON object, nothing else."""

                    # Call OpenAI service for research
                    response_text = openai_service.get_text_completion(
                        research_prompt,
                        model="gpt-4",
                        temperature=0.7
                    )
                    
                    # Parse the research response
                    research_data = parse_research_response(response_text)
                    
                    # Save research data to database
                    if research_data and competitor_id:
                        save_research_data(supabase_service, competitor_id, research_data)
                        research_result = {
                            "competitor_id": competitor_id,
                            "competitor_name": competitor.get("name"),
                            "status": "success",
                            "from_cache": False,  # Indicate this came from OpenAI
                            "networth_count": len(research_data.get("networth", [])),
                            "users_count": len(research_data.get("users", [])),
                            "funding_count": len(research_data.get("funding", [])),
                            # Include actual data for graphs
                            "networth": research_data.get("networth", []),
                            "users": research_data.get("users", []),
                            "funding": research_data.get("funding", [])
                        }
                        research_results.append(research_result)
                        researched_count += 1
                        logger.info(f"Successfully researched and saved data for {competitor.get('name')}")
                        
                        # Send research complete event for this competitor
                        yield f"data: {json.dumps({'type': 'competitor_research', 'result': research_result})}\n\n"
                    else:
                        research_result = {
                            "competitor_id": competitor_id,
                            "competitor_name": competitor.get("name"),
                            "status": "failed",
                            "error": "Could not parse research data"
                        }
                        research_results.append(research_result)
                        researched_count += 1
                        logger.warning(f"Could not parse research data for {competitor.get('name')}")
                        
                        # Send research failed event
                        yield f"data: {json.dumps({'type': 'competitor_research', 'result': research_result})}\n\n"
                    
            except Exception as e:
                logger.error(f"Error researching competitor {competitor.get('name')}: {str(e)}")
                research_result = {
                    "competitor_id": competitor_id,
                    "competitor_name": competitor.get("name"),
                    "status": "error",
                    "error": str(e)
                }
                research_results.append(research_result)
                researched_count += 1
                
                # Send research error event
                yield f"data: {json.dumps({'type': 'competitor_research', 'result': research_result})}\n\n"
        
        # Send completion event
        yield f"data: {json.dumps({'type': 'complete', 'company_url': company_url, 'total_found': len(saved_competitors), 'total_saved': len([c for c in saved_competitors if 'error' not in c]), 'research_results': research_results})}\n\n"
        
    except Exception as e:
        logger.error(f"Error in stream_competitors_research: {str(e)}", exc_info=True)
        yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"


def parse_competitors_response(response_text):
    """
    Parse the OpenAI response to extract the competitors JSON array.
    Handles various response formats including markdown code blocks.
    """
    import re
    
    # Try to find JSON array in the response
    # Look for JSON array pattern
    json_pattern = r'\[[\s\S]*?\]'
    match = re.search(json_pattern, response_text)
    
    if match:
        try:
            json_str = match.group(0)
            competitors = json.loads(json_str)
            
            # Validate and clean the data
            if isinstance(competitors, list):
                # Ensure each item has name and url
                cleaned_competitors = []
                for comp in competitors:
                    if isinstance(comp, dict) and "name" in comp and "url" in comp:
                        cleaned_competitors.append({
                            "name": str(comp["name"]).strip(),
                            "url": str(comp["url"]).strip()
                        })
                return cleaned_competitors
        except json.JSONDecodeError:
            pass
    
    # If JSON parsing failed, try to extract from markdown code blocks
    code_block_pattern = r'```(?:json)?\s*(\[[\s\S]*?\])\s*```'
    match = re.search(code_block_pattern, response_text, re.IGNORECASE)
    
    if match:
        try:
            json_str = match.group(1)
            competitors = json.loads(json_str)
            if isinstance(competitors, list):
                cleaned_competitors = []
                for comp in competitors:
                    if isinstance(comp, dict) and "name" in comp and "url" in comp:
                        cleaned_competitors.append({
                            "name": str(comp["name"]).strip(),
                            "url": str(comp["url"]).strip()
                        })
                return cleaned_competitors
        except json.JSONDecodeError:
            pass
    
    # If all parsing fails, return empty array
    logger.warning(f"Could not parse competitors from response: {response_text[:200]}")
    return []


def parse_research_response(response_text):
    """
    Parse the OpenAI response to extract the research data (networth, users, funding).
    Handles various response formats including markdown code blocks.
    """
    import re
    
    # First, try to extract from markdown code blocks (most common format)
    code_block_patterns = [
        r'```(?:json)?\s*(\{[\s\S]*?\})\s*```',  # Standard code block
        r'```\s*(\{[\s\S]*?\})\s*```',  # Code block without language
    ]
    
    for pattern in code_block_patterns:
        match = re.search(pattern, response_text, re.IGNORECASE | re.DOTALL)
        if match:
            try:
                json_str = match.group(1)
                research_data = json.loads(json_str)
                if isinstance(research_data, dict):
                    # Check if it has the required keys (case-insensitive)
                    result = {}
                    for key in ["networth", "users", "funding"]:
                        # Try exact match first
                        if key in research_data:
                            result[key] = research_data[key]
                        else:
                            # Try case-insensitive match
                            found_key = None
                            for k in research_data.keys():
                                if k.lower() == key.lower():
                                    found_key = k
                                    break
                            result[key] = research_data.get(found_key, []) if found_key else []
                    
                    # Validate arrays are lists
                    if isinstance(result.get("networth"), list) and isinstance(result.get("users"), list) and isinstance(result.get("funding"), list):
                        return result
            except (json.JSONDecodeError, AttributeError) as e:
                logger.debug(f"Failed to parse from code block: {str(e)}")
                continue
    
    # Try to find JSON object in the response (look for opening brace to closing brace)
    # Use a more flexible approach - find the largest JSON object
    brace_count = 0
    start_idx = -1
    
    for i, char in enumerate(response_text):
        if char == '{':
            if brace_count == 0:
                start_idx = i
            brace_count += 1
        elif char == '}':
            brace_count -= 1
            if brace_count == 0 and start_idx != -1:
                try:
                    json_str = response_text[start_idx:i+1]
                    research_data = json.loads(json_str)
                    if isinstance(research_data, dict):
                        # Check if it looks like our research data structure
                        has_arrays = any(
                            isinstance(research_data.get(k, []), list) 
                            for k in ["networth", "users", "funding", "Networth", "Users", "Funding"]
                        )
                        if has_arrays:
                            result = {}
                            for key in ["networth", "users", "funding"]:
                                # Try exact match first
                                if key in research_data:
                                    result[key] = research_data[key]
                                else:
                                    # Try case-insensitive match
                                    found_key = None
                                    for k in research_data.keys():
                                        if k.lower() == key.lower():
                                            found_key = k
                                            break
                                    result[key] = research_data.get(found_key, []) if found_key else []
                            
                            # Validate arrays are lists
                            if isinstance(result.get("networth"), list) and isinstance(result.get("users"), list) and isinstance(result.get("funding"), list):
                                return result
                except (json.JSONDecodeError, AttributeError):
                    pass
                start_idx = -1
    
    # Try pattern matching for JSON with specific keys
    json_patterns = [
        r'\{[\s\S]*?"networth"[\s\S]*?"users"[\s\S]*?"funding"[\s\S]*?\}',
        r'\{[\s\S]*?"Networth"[\s\S]*?"Users"[\s\S]*?"Funding"[\s\S]*?\}',
        r'\{[\s\S]*?networth[\s\S]*?users[\s\S]*?funding[\s\S]*?\}',
    ]
    
    for pattern in json_patterns:
        match = re.search(pattern, response_text, re.IGNORECASE | re.DOTALL)
        if match:
            try:
                json_str = match.group(0)
                research_data = json.loads(json_str)
                if isinstance(research_data, dict):
                    result = {}
                    for key in ["networth", "users", "funding"]:
                        if key in research_data:
                            result[key] = research_data[key]
                        else:
                            found_key = None
                            for k in research_data.keys():
                                if k.lower() == key.lower():
                                    found_key = k
                                    break
                            result[key] = research_data.get(found_key, []) if found_key else []
                    
                    if isinstance(result.get("networth"), list) and isinstance(result.get("users"), list) and isinstance(result.get("funding"), list):
                        return result
            except (json.JSONDecodeError, AttributeError):
                continue
    
    # If all parsing fails, return None
    logger.warning(f"Could not parse research data from response: {response_text[:500]}")
    return None


def save_research_data(supabase_service, company_id, research_data):
    """
    Save research data (networth, users, funding) to the database.
    
    Args:
        supabase_service: Instance of SupabaseService
        company_id: UUID of the company
        research_data: Dictionary with 'networth', 'users', and 'funding' arrays
    """
    try:
        # Save networth records
        for networth_item in research_data.get("networth", []):
            try:
                if isinstance(networth_item, dict) and "value" in networth_item and "year" in networth_item and "source" in networth_item:
                    supabase_service.create_company_networth(
                        company_id=company_id,
                        value_usd=float(networth_item["value"]),
                        year=int(networth_item["year"]),
                        source_url=str(networth_item["source"]).strip()
                    )
            except Exception as e:
                logger.warning(f"Error saving networth record: {str(e)}")
        
        # Save users records
        for users_item in research_data.get("users", []):
            try:
                if isinstance(users_item, dict) and "value" in users_item and "year" in users_item and "source" in users_item:
                    supabase_service.create_company_users(
                        company_id=company_id,
                        value=int(users_item["value"]),
                        year=int(users_item["year"]),
                        source_url=str(users_item["source"]).strip()
                    )
            except Exception as e:
                logger.warning(f"Error saving users record: {str(e)}")
        
        # Save funding records
        for funding_item in research_data.get("funding", []):
            try:
                if isinstance(funding_item, dict) and "value" in funding_item and "year" in funding_item and "source" in funding_item:
                    supabase_service.create_company_funding(
                        company_id=company_id,
                        value_usd=float(funding_item["value"]),
                        year=int(funding_item["year"]),
                        source_url=str(funding_item["source"]).strip()
                    )
            except Exception as e:
                logger.warning(f"Error saving funding record: {str(e)}")
                
    except Exception as e:
        logger.error(f"Error saving research data for company {company_id}: {str(e)}")
        raise
