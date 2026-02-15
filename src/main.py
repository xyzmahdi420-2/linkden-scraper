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
import asyncio

import requests
from requests import Session
from bs4 import BeautifulSoup
from apify import Actor

warnings.filterwarnings("ignore")

# ============================================================================
# CONSTANTS & REGEX PATTERNS
# ============================================================================

COUNTRY_CODES = {
    "United States": "US", "United Kingdom": "GB", "Canada": "CA", "Australia": "AU",
    "India": "IN", "Bangladesh": "BD", "Germany": "DE", "France": "FR", "Spain": "ES",
    "Italy": "IT", "Netherlands": "NL", "Brazil": "BR", "Mexico": "MX", "Singapore": "SG",
    "Japan": "JP", "China": "CN", "South Korea": "KR",
}

# Regex patterns
RE_EMAIL = re.compile(r'"url":"mailto:([^"]+)"')
RE_NAME = re.compile(r'displayImageWithFrameReference":null,"a11yText":"([^"]+)"')
RE_NAME2 = re.compile(r'"originalImageUrn"\s*:\s*null\s*,\s*"a11yText"\s*:\s*"([^"]*)"')
RE_WEBSITES = re.compile(r'https?://[^\s"<]+')
RE_FSD = re.compile(r'elements":\["urn:li:fsd_profile:([^"]+)"')
RE_LOCATION = re.compile(r'"children":\["([^"]+)"\]')
RE_OR_LOCATION = re.compile(r'"defaultLocalizedName":"([^"]+)"')
RE_ABOUT = re.compile(r'"numInitialLinesToShow":4,"text":\{"textDirection":"USER_LOCALE","text":"((?:\\.|[^"\\])*)","attributesV2')
RE_FOLLOWER = re.compile(r'"followerCount":(\d+)')
RE_CONNECTIONS = re.compile(r'"connections":{"paging":{"count":\d+,"start":\d+,"total":(\d+),"')
RE_FIRST_NAME = re.compile(r':null,"firstName":"([^"]+)","')
RE_LAST_NAME = re.compile(r'"lastName":"([^"]+)","memorialized":([a-z]+),"profileTopCardCustomAction"')
RE_HEADLINE = re.compile(r'"companyNameOnProfileTopCardShown":true,"headline":"([^"]+)"')
RE_EMP_TYPE = re.compile(r'·\s*(Full-time|Part-time|Contract|Internship|Freelance|Self-employed)', re.I)
RE_WORK_TYPE = re.compile(r'\b(Remote|On-site|Onsite|Hybrid)\b', re.I)
RE_DATE = re.compile(r'([A-Za-z]+\s+\d{4}|\d{4})\s*[-–]\s*(Present|[A-Za-z]+\s+\d{4}|\d{4})?')
RE_COMPANY_ID = re.compile(r'/company/(\d+)')
RE_LOGO = re.compile(r'company-logo[^"]*?/(\d+)/[^"]*logo[^"]*')

CARDS_ID = '55af784c21dc8640b500ab5b45937064'
PROFILES_ID = 'a1a483e719b20537a256b6853cdca711'
BLOCKED_DOMAINS = ('linkedin.com', 'media.licdn.com')


def format_cookies(cookie_string: str) -> Dict[str, str]:
    """Convert cookie string to dictionary."""
    cookies = {}
    for item in cookie_string.split(';'):
        if '=' in item:
            key, value = item.strip().split('=', 1)
            cookies[key.strip()] = value.strip()
    return cookies


def parse_date(text: str) -> Dict:
    """Parse duration string."""
    if not text:
        return {"duration": text, "start_date": {}, "end_date": {}, "is_current": False}
    
    result = {"duration": text, "start_date": {}, "end_date": {}, "is_current": "Present" in text}
    match = RE_DATE.search(text)
    if not match:
        return result
    
    start, end = match.group(1), match.group(2) or "Present"
    
    # Parse dates
    for date_str, date_key in [(start, "start_date"), (end if end != "Present" else None, "end_date")]:
        if not date_str:
            continue
        year_match = re.search(r'(\d{4})', date_str)
        month_match = re.search(r'([A-Za-z]+)', date_str)
        if year_match:
            result[date_key]["year"] = int(year_match.group(1))
        if month_match:
            try:
                result[date_key]["month"] = datetime.strptime(month_match.group(1)[:3], '%b').month
            except:
                pass
    
    return result


class LinkedInProfileScraper:
    """LinkedIn profile scraper."""
    
    def __init__(self, username: str, cookies: str):
        self.username = username
        self.cookies = format_cookies(cookies)
        self.session = Session()
        self.session.verify = False
        
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0"
        self.headers = {
            'user-agent': user_agent,
            'referer': 'https://www.linkedin.com/',
        }
        self.voyager_headers = {
            'accept': 'application/vnd.linkedin.normalized+json+2.1',
            'csrf-token': self.cookies.get('JSESSIONID', '').strip('"'),
            'user-agent': user_agent,
            'x-restli-protocol-version': '2.0.0',
        }
        
        self._contact_info = None
        self._decoded_html = None
        self.fsd_profile = None
    
    def _get_decoded_html(self) -> str:
        if self._decoded_html is None:
            url = f'https://www.linkedin.com/in/{self.username}/overlay/contact-info/'
            response = self.session.get(url, cookies=self.cookies, headers=self.headers)
            response.raise_for_status()
            self._decoded_html = html.unescape(response.text).encode('utf-8').decode('unicode_escape')
        return self._decoded_html
    
    def _extract_basic_info(self) -> Dict:
        decoded = self._get_decoded_html()
        
        name_match = RE_NAME.search(decoded) or RE_NAME2.search(decoded)
        fullname = name_match.group(1).replace(' is open to work', '') if name_match else None
        
        email_match = RE_EMAIL.search(decoded)
        email = email_match.group(1) if email_match else None
        
        soup = BeautifulSoup(decoded, 'html.parser')
        websites = [s for s in RE_WEBSITES.findall(soup.get_text()) if not any(b in s for b in BLOCKED_DOMAINS)]
        
        fsd_match = RE_FSD.search(decoded)
        if fsd_match:
            self.fsd_profile = fsd_match.group(1)
        
        location = None
        for loc in RE_LOCATION.findall(decoded):
            if COUNTRY_CODES.get(loc.rsplit(",", 1)[-1].strip()):
                location = loc
                break
        if not location:
            or_locations = RE_OR_LOCATION.findall(decoded)
            location = or_locations[-1] if or_locations else None
        
        return {'fullname': fullname, 'email': email, 'websites': websites, 'location': location, 'name_match': name_match}
    
    def _fetch_profile_data(self) -> Tuple[str, str]:
        prof_url = f'https://www.linkedin.com/voyager/api/graphql?includeWebMetadata=true&variables=(vanityName:{self.username})&queryId=voyagerIdentityDashProfiles.{PROFILES_ID}'
        prof_resp = self.session.get(prof_url, cookies=self.cookies, headers=self.voyager_headers)
        prof_resp.raise_for_status()
        prof_text = prof_resp.text
        
        if not self.fsd_profile:
            fsd_match = RE_FSD.search(prof_text)
            if fsd_match:
                self.fsd_profile = fsd_match.group(1)
            else:
                raise ValueError("Could not extract FSD profile ID")
        
        cards_url = f'https://www.linkedin.com/voyager/api/graphql?variables=(profileUrn:urn%3Ali%3Afsd_profile%3A{self.fsd_profile})&queryId=voyagerIdentityDashProfileCards.{CARDS_ID}'
        cards_resp = self.session.get(cards_url, cookies=self.cookies, headers=self.voyager_headers)
        cards_resp.raise_for_status()
        
        return prof_text, cards_resp.text
    
    def _parse_experience(self, entity: Dict, logos: Dict[str, str]) -> Optional[Dict]:
        if not entity:
            return None
        
        exp = {
            "title": None, "company": None, "employment_type": None, "location": None,
            "work_type": None, "duration": None, "start_date": {}, "is_current": False,
            "company_linkedin_url": None, "company_logo_url": None, "company_id": None
        }
        
        title_v2 = entity.get("titleV2") or {}
        text_obj = title_v2.get("text") or {}
        exp["title"] = text_obj.get("text") if isinstance(text_obj, dict) else None
        
        subtitle = entity.get("subtitle") or {}
        subtitle_text = subtitle.get("text", "")
        if subtitle_text:
            emp_match = RE_EMP_TYPE.search(subtitle_text)
            if emp_match:
                exp["employment_type"] = emp_match.group(1)
            exp["company"] = re.sub(r'\s*·\s*(Full-time|Part-time|Contract|Internship|Freelance|Self-employed).*', '', subtitle_text, flags=re.I).strip() or None
        
        caption = entity.get("caption") or {}
        caption_text = caption.get("text", "")
        date_info = parse_date(caption_text)
        exp.update({"duration": date_info["duration"], "start_date": date_info["start_date"], "is_current": date_info["is_current"]})
        if date_info["end_date"]:
            exp["end_date"] = date_info["end_date"]
        
        metadata = entity.get("metadata") or {}
        metadata_text = metadata.get("text", "")
        if metadata_text:
            exp["location"] = metadata_text
            work_type_match = RE_WORK_TYPE.search(metadata_text)
            if work_type_match:
                work_type = work_type_match.group(1)
                exp["work_type"] = "On-site" if work_type.lower() == "onsite" else work_type
                exp["location"] = re.sub(r'\s*\(?(Remote|On-site|Onsite|Hybrid)\)?\s*', '', metadata_text, flags=re.I).strip() or None
        
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
    
    def _extract_experiences(self, cards_data: Dict, cards_text: str) -> List[Dict]:
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
        
        seen: Set[Tuple] = set()
        result = []
        for exp in experiences:
            key = (exp["title"], exp["company"], exp.get("start_date", {}).get("year"))
            if key not in seen:
                seen.add(key)
                cleaned = {k: v for k, v in exp.items() if v not in (None, {}, "")}
                result.append(cleaned)
        
        return result
    
    def get_profile(self) -> Dict:
        basic = self._extract_basic_info()
        decoded = self._get_decoded_html()
        prof_text, cards_text = self._fetch_profile_data()
        cards_data = json.loads(cards_text) if cards_text else {}
        
        first_name_match = RE_FIRST_NAME.search(prof_text)
        last_name_match = RE_LAST_NAME.search(prof_text)
        headline_match = RE_HEADLINE.search(prof_text)
        about_match = RE_ABOUT.search(cards_text)
        follower_match = RE_FOLLOWER.search(prof_text)
        connections_match = RE_CONNECTIONS.search(prof_text)
        
        country = None
        city = None
        country_code = None
        if basic['location'] and "," in basic['location']:
            country = basic['location'].rsplit(",", 1)[-1].strip()
            city = ','.join(basic['location'].split(",")[:-1])
            country_code = COUNTRY_CODES.get(country)
        
        soup = BeautifulSoup(decoded, 'html.parser')
        title_tag = soup.find('title')
        title_fullname = title_tag.text.replace(' | LinkedIn', '') if title_tag else None
        
        return {
            "basic_info": {
                "fullname": (f"{first_name_match.group(1)} {last_name_match.group(1)}" if first_name_match and last_name_match else title_fullname or basic['fullname']),
                "first_name": first_name_match.group(1) if first_name_match else None,
                "last_name": last_name_match.group(1) if last_name_match else None,
                "headline": headline_match.group(1) if headline_match else None,
                "public_identifier": self.username,
                "profile_url": f"https://linkedin.com/in/{self.username}",
                "about": about_match.group(1) if about_match else None,
                "location": {"country": country, "full": basic['location'], "city": city, "country_code": country_code},
                "is_creator": '"creator":true,"verificationData' in prof_text,
                "is_premium": '"premium":true' in decoded or 'is a Premium member' in decoded,
                "open_to_work": 'is open to work' in basic['name_match'].group(1) if basic['name_match'] else False,
                "is_remembrance": '"memorialized":true' in prof_text or 'In remembrance' in decoded,
                "urn": self.fsd_profile,
                "follower_count": int(follower_match.group(1)) if follower_match else None,
                "connection_count": int(connections_match.group(1)) if connections_match else None,
                "email": basic['email'],
                "websites": basic['websites'],
            },
            "experience": self._extract_experiences(cards_data, cards_text)
        }


async def main():
    """Apify actor entry point."""
    async with Actor:
        actor_input = await Actor.get_input() or {}
        profiles = actor_input.get('profiles', [])
        cookies = actor_input.get('cookies')
        
        if not cookies:
            await Actor.fail('LinkedIn cookies required.')
            return
        
        if not profiles:
            await Actor.fail('No profiles specified.')
            return
        
        await Actor.log.info(f'Starting scrape for {len(profiles)} profile(s)')
        
        for idx, profile_input in enumerate(profiles, 1):
            if isinstance(profile_input, str):
                username = profile_input
            elif isinstance(profile_input, dict):
                username = profile_input.get('username') or profile_input.get('url', '').split('/in/')[-1].strip('/')
            else:
                await Actor.log.warning(f'Invalid profile at index {idx}')
                continue
            
            username = username.strip().rstrip('/')
            if '/in/' in username:
                username = username.split('/in/')[-1].strip('/')
            
            await Actor.log.info(f'[{idx}/{len(profiles)}] Scraping: {username}')
            
            try:
                scraper = LinkedInProfileScraper(username, cookies)
                profile_data = scraper.get_profile()
                profile_data['scraped_at'] = datetime.utcnow().isoformat()
                profile_data['scrape_status'] = 'success'
                await Actor.push_data(profile_data)
                await Actor.log.info(f'✓ Success: {username}')
            except Exception as e:
                error_msg = f'Error: {username}: {str(e)}'
                await Actor.log.error(error_msg)
                await Actor.push_data({
                    'username': username,
                    'scrape_status': 'failed',
                    'error': error_msg,
                    'scraped_at': datetime.utcnow().isoformat()
                })
        
        await Actor.log.info('Scraping completed!')
