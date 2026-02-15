"""
LinkedIn Profile Scraper - Apify Actor
Scrapes LinkedIn profiles with full experience data
"""

import re
import json
import html
from typing import Dict, List, Optional, Set, Tuple
from datetime import datetime
import warnings

import requests
from requests import Session
from bs4 import BeautifulSoup
from apify import Actor

warnings.filterwarnings("ignore")

# ============================================================================
# CONSTANTS & REGEX PATTERNS
# ============================================================================

COUNTRY_CODES = {
    "United States": "US",
    "United Kingdom": "GB",
    "Canada": "CA",
    "Australia": "AU",
    "India": "IN",
    "Bangladesh": "BD",
    "Germany": "DE",
    "France": "FR",
    "Spain": "ES",
    "Italy": "IT",
    "Netherlands": "NL",
    "Brazil": "BR",
    "Mexico": "MX",
    "Singapore": "SG",
    "Japan": "JP",
    "China": "CN",
    "South Korea": "KR",
}

# Profile extraction patterns
RE_EMAIL = re.compile(r'"url":"mailto:([^"]+)"')
RE_NAME = re.compile(r'displayImageWithFrameReference":null,"a11yText":"([^"]+)"')
RE_NAME2 = re.compile(r'"originalImageUrn"\s*:\s*null\s*,\s*"a11yText"\s*:\s*"([^"]*)"')
RE_WEBSITES = re.compile(r'https?://[^\s"<]+')
RE_FSD = re.compile(r'elements":\["urn:li:fsd_profile:([^"]+)"')
RE_LOCATION = re.compile(r'"children":\["([^"]+)"\]')
RE_OR_LOCATION = re.compile(r'"defaultLocalizedName":"([^"]+)"')
RE_COUNTRY = re.compile(r'"countryISOCode":"([^"]+)"')
RE_ABOUT = re.compile(r'"numInitialLinesToShow":4,"text":\{"textDirection":"USER_LOCALE","text":"((?:\\.|[^"\\])*)","attributesV2')
RE_FOLLOWER = re.compile(r'"followerCount":(\d+)')
RE_CONNECTIONS = re.compile(r'"connections":{"paging":{"count":\d+,"start":\d+,"total":(\d+),"')
RE_FIRST_NAME = re.compile(r':null,"firstName":"([^"]+)","')
RE_LAST_NAME = re.compile(r'"lastName":"([^"]+)","memorialized":([a-z]+),"profileTopCardCustomAction"')
RE_HEADLINE = re.compile(r'"companyNameOnProfileTopCardShown":true,"headline":"([^"]+)"')

# Experience extraction patterns
RE_EMP_TYPE = re.compile(r'·\s*(Full-time|Part-time|Contract|Internship|Freelance|Self-employed)', re.I)
RE_WORK_TYPE = re.compile(r'\b(Remote|On-site|Onsite|Hybrid)\b', re.I)
RE_DATE = re.compile(r'([A-Za-z]+\s+\d{4}|\d{4})\s*[-–]\s*(Present|[A-Za-z]+\s+\d{4}|\d{4})?')
RE_COMPANY_ID = re.compile(r'/company/(\d+)')
RE_LOGO = re.compile(r'company-logo[^"]*?/(\d+)/[^"]*logo[^"]*')

# Static IDs
CARDS_ID = '55af784c21dc8640b500ab5b45937064'
PROFILES_ID = 'a1a483e719b20537a256b6853cdca711'

BLOCKED_DOMAINS = ('linkedin.com', 'media.licdn.com')


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def format_cookies(cookie_string: str) -> Dict[str, str]:
    """Convert cookie string to dictionary format."""
    cookies = {}
    for item in cookie_string.split(';'):
        item = item.strip()
        if '=' in item:
            key, value = item.split('=', 1)
            cookies[key.strip()] = value.strip()
    return cookies


def generate_chrome_user_agent() -> str:
    """Generate a realistic Chrome user agent."""
    return "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"


def parse_date(text: str) -> Dict:
    """Parse duration string into structured data."""
    if not text:
        return {"duration": text, "start_date": {}, "end_date": {}, "is_current": False}
    
    result = {
        "duration": text,
        "start_date": {},
        "end_date": {},
        "is_current": "Present" in text
    }
    
    match = RE_DATE.search(text)
    if not match:
        return result
    
    start, end = match.group(1), match.group(2) or "Present"
    
    # Parse start date
    year_match = re.search(r'(\d{4})', start)
    month_match = re.search(r'([A-Za-z]+)', start)
    if year_match:
        result["start_date"]["year"] = int(year_match.group(1))
    if month_match:
        try:
            result["start_date"]["month"] = datetime.strptime(month_match.group(1)[:3], '%b').month
        except:
            pass
    
    # Parse end date
    if end != "Present":
        year_match = re.search(r'(\d{4})', end)
        month_match = re.search(r'([A-Za-z]+)', end)
        if year_match:
            result["end_date"]["year"] = int(year_match.group(1))
        if month_match:
            try:
                result["end_date"]["month"] = datetime.strptime(month_match.group(1)[:3], '%b').month
            except:
                pass
    
    return result


# ============================================================================
# MAIN SCRAPER CLASS
# ============================================================================

class LinkedInProfileScraper:
    """Fast and efficient LinkedIn profile scraper."""
    
    def __init__(self, username: str, cookies: str):
        """Initialize scraper with username and cookies."""
        self.username = username
        self.cookies = format_cookies(cookies)
        self.session = Session()
        self.session.verify = False
        
        # Set up headers
        user_agent = generate_chrome_user_agent()
        self.headers = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'accept-language': 'en-US,en;q=0.9',
            'user-agent': user_agent,
            'referer': 'https://www.linkedin.com/',
        }
        
        self.voyager_headers = {
            'accept': 'application/vnd.linkedin.normalized+json+2.1',
            'accept-language': 'en-US,en;q=0.9',
            'csrf-token': self.cookies.get('JSESSIONID', '').strip('"'),
            'user-agent': user_agent,
            'x-li-lang': 'en_US',
            'x-restli-protocol-version': '2.0.0',
        }
        
        # Cache for profile data
        self._contact_info = None
        self._decoded_html = None
        self.fsd_profile = None
    
    def _fetch_contact_info(self) -> str:
        """Fetch and cache contact information page."""
        if self._contact_info is None:
            url = f'https://www.linkedin.com/in/{self.username}/overlay/contact-info/'
            response = self.session.get(url, cookies=self.cookies, headers=self.headers)
            response.raise_for_status()
            self._contact_info = response.text
        return self._contact_info
    
    def _get_decoded_html(self) -> str:
        """Get decoded and unescaped HTML."""
        if self._decoded_html is None:
            contact_html = self._fetch_contact_info()
            self._decoded_html = html.unescape(contact_html).encode('utf-8').decode('unicode_escape')
        return self._decoded_html
    
    def _extract_basic_info(self) -> Dict:
        """Extract basic profile information from contact page."""
        decoded = self._get_decoded_html()
        
        # Name
        name_match = RE_NAME.search(decoded) or RE_NAME2.search(decoded)
        fullname = name_match.group(1).replace(' is open to work', '') if name_match else None
        
        # Email
        email_match = RE_EMAIL.search(decoded)
        email = email_match.group(1) if email_match else None
        
        # Websites
        soup = BeautifulSoup(decoded, 'html.parser')
        websites = RE_WEBSITES.findall(soup.get_text())
        websites = [s for s in websites if not any(b in s for b in BLOCKED_DOMAINS)]
        
        # FSD Profile ID
        fsd_match = RE_FSD.search(decoded)
        if fsd_match:
            self.fsd_profile = fsd_match.group(1)
        
        # Location
        location = None
        location_matches = RE_LOCATION.findall(decoded)
        for loc in location_matches:
            country = loc.rsplit(",", 1)[-1].strip()
            if COUNTRY_CODES.get(country):
                location = loc
                break
        
        if not location:
            or_locations = RE_OR_LOCATION.findall(decoded)
            location = or_locations[-1] if or_locations else None
        
        return {
            'fullname': fullname,
            'email': email,
            'websites': websites,
            'location': location,
            'name_match': name_match
        }
    
    def _fetch_profile_data(self) -> Tuple[str, str]:
        """Fetch profile and cards data from LinkedIn API."""
        # Fetch profile data
        prof_url = (
            f'https://www.linkedin.com/voyager/api/graphql'
            f'?includeWebMetadata=true'
            f'&variables=(vanityName:{self.username})'
            f'&queryId=voyagerIdentityDashProfiles.{PROFILES_ID}'
        )
        
        prof_resp = self.session.get(
            prof_url,
            cookies=self.cookies,
            headers=self.voyager_headers
        )
        prof_resp.raise_for_status()
        prof_text = prof_resp.text
        
        # Extract FSD if not already set
        if not self.fsd_profile:
            fsd_match = RE_FSD.search(prof_text)
            if fsd_match:
                self.fsd_profile = fsd_match.group(1)
            else:
                raise ValueError("Could not extract FSD profile ID")
        
        # Fetch cards data
        cards_url = (
            f'https://www.linkedin.com/voyager/api/graphql'
            f'?variables=(profileUrn:urn%3Ali%3Afsd_profile%3A{self.fsd_profile})'
            f'&queryId=voyagerIdentityDashProfileCards.{CARDS_ID}'
        )
        
        cards_resp = self.session.get(
            cards_url,
            cookies=self.cookies,
            headers=self.voyager_headers
        )
        cards_resp.raise_for_status()
        
        return prof_text, cards_resp.text
    
    def _extract_experiences(self, cards_data: Dict, cards_text: str) -> List[Dict]:
        """Extract work experience from cards data."""
        # Extract company logos
        logos = {}
        for match in RE_LOGO.finditer(cards_text):
            company_id = match.group(1)
            logo_pattern = rf'(https://media\.licdn\.com/dms/image/[^"]*company-logo[^"]*{company_id}[^"]*)'
            logo_match = re.search(logo_pattern, cards_text)
            if logo_match:
                logos[company_id] = logo_match.group(1)
        
        experiences = []
        included = cards_data.get("data", {}).get("included", []) or cards_data.get("included", [])
        
        for item in included:
            urn = item.get("entityUrn", "")
            if "EXPERIENCE" not in urn or "fsd_profileCard" not in urn:
                continue
            
            for comp in item.get("topComponents", []):
                fixed_list = comp.get("components", {}).get("fixedListComponent")
                if not fixed_list:
                    continue
                
                for list_item in fixed_list.get("components", []):
                    entity = list_item.get("components", {}).get("entityComponent")
                    if not entity:
                        continue
                    
                    exp = self._parse_experience(entity, logos)
                    if not exp:
                        continue
                    
                    # Handle nested positions (multiple roles at same company)
                    sub_components = (entity.get("subComponents") or {}).get("components", [])
                    
                    if sub_components:
                        parent_info = (exp["title"], exp["company_linkedin_url"], exp["company_id"])
                        has_nested = False
                        
                        for nested in sub_components:
                            nested_entity = (nested.get("components") or {}).get("entityComponent")
                            if nested_entity:
                                nested_exp = self._parse_experience(nested_entity, logos)
                                if not nested_exp:
                                    continue
                                
                                # Inherit parent company info if missing
                                if not nested_exp["company"] or "mos" in str(nested_exp.get("company", "")) or "yrs" in str(nested_exp.get("company", "")):
                                    nested_exp["company"] = parent_info[0]
                                nested_exp["company_linkedin_url"] = nested_exp["company_linkedin_url"] or parent_info[1]
                                nested_exp["company_id"] = nested_exp["company_id"] or parent_info[2]
                                
                                if parent_info[2] and parent_info[2] in logos:
                                    nested_exp["company_logo_url"] = logos[parent_info[2]]
                                
                                if nested_exp["title"]:
                                    experiences.append(nested_exp)
                                    has_nested = True
                        
                        if not has_nested and exp["title"]:
                            experiences.append(exp)
                    elif exp["title"]:
                        experiences.append(exp)
        
        # Deduplicate
        seen: Set[Tuple] = set()
        result = []
        for exp in experiences:
            key = (exp["title"], exp["company"], exp.get("start_date", {}).get("year"))
            if key not in seen:
                seen.add(key)
                # Remove None and empty values
                cleaned = {k: v for k, v in exp.items() if v not in (None, {}, "")}
                result.append(cleaned)
        
        return result
    
    def _parse_experience(self, entity: Dict, logos: Dict[str, str]) -> Optional[Dict]:
        """Parse a single experience entity."""
        if not entity:
            return None
        
        exp = {
            "title": None,
            "company": None,
            "employment_type": None,
            "location": None,
            "work_type": None,
            "duration": None,
            "start_date": {},
            "is_current": False,
            "company_linkedin_url": None,
            "company_logo_url": None,
            "company_id": None
        }
        
        # Title
        title_v2 = entity.get("titleV2") or {}
        text_obj = title_v2.get("text") or {}
        exp["title"] = text_obj.get("text") if isinstance(text_obj, dict) else None
        
        # Company & employment type
        subtitle = entity.get("subtitle") or {}
        subtitle_text = subtitle.get("text", "") if subtitle else ""
        if subtitle_text:
            emp_match = RE_EMP_TYPE.search(subtitle_text)
            if emp_match:
                exp["employment_type"] = emp_match.group(1)
            exp["company"] = re.sub(
                r'\s*·\s*(Full-time|Part-time|Contract|Internship|Freelance|Self-employed).*',
                '', subtitle_text, flags=re.I
            ).strip() or None
        
        # Duration
        caption = entity.get("caption") or {}
        caption_text = caption.get("text", "") if caption else ""
        date_info = parse_date(caption_text)
        exp.update({
            "duration": date_info["duration"],
            "start_date": date_info["start_date"],
            "is_current": date_info["is_current"]
        })
        if date_info["end_date"]:
            exp["end_date"] = date_info["end_date"]
        
        # Location & work type
        metadata = entity.get("metadata") or {}
        metadata_text = metadata.get("text", "") if metadata else ""
        if metadata_text:
            exp["location"] = metadata_text
            work_type_match = RE_WORK_TYPE.search(metadata_text)
            if work_type_match:
                work_type = work_type_match.group(1)
                exp["work_type"] = "On-site" if work_type.lower() == "onsite" else work_type
                exp["location"] = re.sub(
                    r'\s*\(?(Remote|On-site|Onsite|Hybrid)\)?\s*',
                    '', metadata_text, flags=re.I
                ).strip() or None
        
        # Company URL and logo
        image = entity.get("image") or {}
        action_target = (image.get("actionTarget", "") if image else "") or entity.get("textActionTarget", "")
        if action_target and "/company/" in action_target:
            exp["company_linkedin_url"] = action_target
            company_id_match = RE_COMPANY_ID.search(action_target)
            if company_id_match:
                company_id = company_id_match.group(1)
                exp["company_id"] = company_id
                if company_id in logos:
                    exp["company_logo_url"] = logos[company_id]
        
        return exp
    
    def get_profile(self) -> Dict:
        """Get complete profile information."""
        # Extract basic info
        basic = self._extract_basic_info()
        decoded = self._get_decoded_html()
        
        # Fetch API data
        prof_text, cards_text = self._fetch_profile_data()
        cards_data = json.loads(cards_text) if cards_text else {}
        
        # Extract additional fields
        first_name_match = RE_FIRST_NAME.search(prof_text)
        last_name_match = RE_LAST_NAME.search(prof_text)
        headline_match = RE_HEADLINE.search(prof_text)
        about_match = RE_ABOUT.search(cards_text)
        follower_match = RE_FOLLOWER.search(prof_text)
        connections_match = RE_CONNECTIONS.search(prof_text)
        
        # Parse location
        country = None
        city = None
        country_code = None
        if basic['location'] and "," in basic['location']:
            country = basic['location'].rsplit(",", 1)[-1].strip()
            city = ','.join(basic['location'].split(",")[:-1])
            country_code = COUNTRY_CODES.get(country)
        
        # Get full name from title tag if needed
        soup = BeautifulSoup(decoded, 'html.parser')
        title_tag = soup.find('title')
        title_fullname = title_tag.text.replace(' | LinkedIn', '') if title_tag else None
        
        # Build final response
        return {
            "basic_info": {
                "fullname": (
                    f"{first_name_match.group(1)} {last_name_match.group(1)}"
                    if first_name_match and last_name_match
                    else title_fullname or basic['fullname']
                ),
                "first_name": first_name_match.group(1) if first_name_match else None,
                "last_name": last_name_match.group(1) if last_name_match else None,
                "headline": headline_match.group(1) if headline_match else None,
                "public_identifier": self.username,
                "profile_url": f"https://linkedin.com/in/{self.username}",
                "about": about_match.group(1) if about_match else None,
                "location": {
                    "country": country,
                    "full": basic['location'],
                    "city": city,
                    "country_code": country_code
                },
                "is_creator": '"creator":true,"verificationData' in prof_text,
                "is_premium": (
                    '"premium":true' in decoded or
                    'is a Premium member' in decoded
                ),
                "open_to_work": (
                    'is open to work' in basic['name_match'].group(1)
                    if basic['name_match'] else False
                ),
                "is_remembrance": (
                    '"memorialized":true' in prof_text or
                    'In remembrance' in decoded
                ),
                "urn": self.fsd_profile,
                "follower_count": int(follower_match.group(1)) if follower_match else None,
                "connection_count": int(connections_match.group(1)) if connections_match else None,
                "email": basic['email'],
                "websites": basic['websites'],
            },
            "experience": self._extract_experiences(cards_data, cards_text)
        }


# ============================================================================
# APIFY ACTOR MAIN
# ============================================================================

async def main():
    """Main Apify actor entry point."""
    async with Actor:
        # Get input
        actor_input = await Actor.get_input() or {}
        
        # Extract profiles to scrape
        profiles = actor_input.get('profiles', [])
        cookies = actor_input.get('cookies')
        
        # Validation
        if not cookies:
            await Actor.fail('LinkedIn cookies are required. Please provide valid session cookies.')
            return
        
        if not profiles:
            await Actor.fail('No profiles to scrape. Please provide a list of LinkedIn usernames.')
            return
        
        # Log start
        await Actor.log.info(f'Starting scrape for {len(profiles)} profile(s)')
        
        # Process each profile
        for idx, profile_input in enumerate(profiles, 1):
            # Handle both string and object inputs
            if isinstance(profile_input, str):
                username = profile_input
            elif isinstance(profile_input, dict):
                username = profile_input.get('username') or profile_input.get('url', '').split('/in/')[-1].strip('/')
            else:
                await Actor.log.warning(f'Invalid profile format at index {idx}, skipping')
                continue
            
            # Clean username
            username = username.strip().rstrip('/')
            if '/in/' in username:
                username = username.split('/in/')[-1].strip('/')
            
            await Actor.log.info(f'[{idx}/{len(profiles)}] Scraping profile: {username}')
            
            try:
                # Scrape profile
                scraper = LinkedInProfileScraper(username, cookies)
                profile_data = scraper.get_profile()
                
                # Add metadata
                profile_data['scraped_at'] = datetime.utcnow().isoformat()
                profile_data['scrape_status'] = 'success'
                
                # Push to dataset
                await Actor.push_data(profile_data)
                await Actor.log.info(f'✓ Successfully scraped: {username}')
                
            except requests.exceptions.HTTPError as e:
                error_msg = f'HTTP error for {username}: {str(e)}'
                await Actor.log.error(error_msg)
                await Actor.push_data({
                    'username': username,
                    'scrape_status': 'failed',
                    'error': error_msg,
                    'scraped_at': datetime.utcnow().isoformat()
                })
                
            except Exception as e:
                error_msg = f'Error scraping {username}: {str(e)}'
                await Actor.log.error(error_msg)
                await Actor.push_data({
                    'username': username,
                    'scrape_status': 'failed',
                    'error': error_msg,
                    'scraped_at': datetime.utcnow().isoformat()
                })
        
        await Actor.log.info('Scraping completed!')
