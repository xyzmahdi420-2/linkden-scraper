# LinkedIn Profile Scraper

Extract comprehensive LinkedIn profile data including experience, education, skills, and contact information in structured JSON format.

## Features ✨

- **Complete Profile Data**: Scrape full names, headlines, locations, about sections, and more
- **Work Experience**: Detailed employment history with company names, roles, dates, and locations
- **Contact Information**: Email addresses and personal websites
- **Network Stats**: Follower counts and connection counts
- **Company Logos**: Direct URLs to company logo images
- **Fast & Reliable**: Optimized scraping with minimal API calls
- **Structured Output**: Clean JSON format ready for analysis or integration

## What You Get 📊

For each LinkedIn profile, the scraper extracts:

### Basic Information
- Full name (first name + last name)
- Professional headline
- Location (city, country, country code)
- About/bio section
- Profile URL and public identifier
- Premium status
- Creator mode status
- "Open to work" status

### Contact Details
- Email address (if publicly available)
- Personal websites and social links

### Network Information
- Total connections
- Follower count

### Work Experience
For each position:
- Job title
- Company name
- Employment type (Full-time, Part-time, Contract, etc.)
- Work arrangement (Remote, Hybrid, On-site)
- Location
- Start and end dates (with month/year breakdown)
- Duration
- Current position indicator
- Company LinkedIn URL
- Company logo URL
- Company ID

## How to Use 🚀

### 1. Get Your LinkedIn Cookies

You need valid LinkedIn session cookies to use this scraper:

1. Log into LinkedIn in your browser
2. Open Developer Tools (F12)
3. Go to Application > Cookies > https://www.linkedin.com
4. Copy the entire cookie string or at minimum these two cookies:
   - `li_at` (your session token)
   - `JSESSIONID` (session ID)

**Example cookie format:**
```
li_at=YOUR_TOKEN_HERE; JSESSIONID=ajax:1234567890; bcookie=v=2&abc123...
```

⚠️ **Important**: Keep your cookies private! They provide access to your LinkedIn account.

### 2. Prepare Profile List

Add the LinkedIn profiles you want to scrape. You can use:
- Usernames: `williamhgates`
- Profile URLs: `https://linkedin.com/in/williamhgates`
- Mix of both

**Example input:**
```json
{
  "profiles": [
    "williamhgates",
    "satyanadella",
    "https://linkedin.com/in/jeff-weiner"
  ],
  "cookies": "li_at=YOUR_COOKIE_HERE; JSESSIONID=ajax:123456789"
}
```

### 3. Run the Actor

Click "Start" and wait for the scraper to collect all profile data. Results are saved to the dataset in JSON format.

## Output Format 📝

```json
{
  "basic_info": {
    "fullname": "Bill Gates",
    "first_name": "Bill",
    "last_name": "Gates",
    "headline": "Co-chair, Bill & Melinda Gates Foundation",
    "public_identifier": "williamhgates",
    "profile_url": "https://linkedin.com/in/williamhgates",
    "about": "Co-chair of the Bill & Melinda Gates Foundation...",
    "location": {
      "country": "United States",
      "full": "Seattle, Washington, United States",
      "city": "Seattle, Washington",
      "country_code": "US"
    },
    "is_creator": false,
    "is_premium": true,
    "open_to_work": false,
    "is_remembrance": false,
    "urn": "ACoAAAB1234",
    "follower_count": 37500000,
    "connection_count": 500,
    "email": "info@gatesventuresllc.com",
    "websites": [
      "https://www.gatesnotes.com",
      "https://www.gatesfoundation.org"
    ]
  },
  "experience": [
    {
      "title": "Co-chair",
      "company": "Bill & Melinda Gates Foundation",
      "employment_type": "Full-time",
      "location": "Seattle, Washington",
      "work_type": "On-site",
      "duration": "Jan 2000 - Present · 25 yrs",
      "start_date": {
        "year": 2000,
        "month": 1
      },
      "is_current": true,
      "company_linkedin_url": "https://www.linkedin.com/company/bill-&-melinda-gates-foundation",
      "company_logo_url": "https://media.licdn.com/dms/image/.../logo.png",
      "company_id": "12345"
    }
  ],
  "scraped_at": "2024-02-15T10:30:00.000Z",
  "scrape_status": "success"
}
```

## Use Cases 💼

- **Recruitment**: Find and evaluate potential candidates
- **Lead Generation**: Build targeted prospect lists for B2B sales
- **Market Research**: Analyze industry professionals and trends
- **Competitive Intelligence**: Research competitors' team composition
- **Network Analysis**: Study professional networks and connections
- **Data Enrichment**: Enhance CRM records with LinkedIn data
- **Academic Research**: Study career patterns and professional mobility

## Pricing 💰

This actor charges based on compute units used. Typically:
- ~0.001-0.003 compute units per profile
- 1,000 profiles ≈ $0.25-$0.75 USD

Exact cost depends on profile complexity and network conditions.

## Important Notes ⚠️

### Legal & Ethical Considerations

- **LinkedIn Terms of Service**: Web scraping may violate LinkedIn's Terms of Service. Use at your own risk.
- **Rate Limits**: Don't scrape too aggressively. LinkedIn may block your account.
- **Personal Data**: Respect privacy. Only scrape public information.
- **Cookie Security**: Never share your LinkedIn cookies publicly.
- **Commercial Use**: Check local laws regarding commercial use of scraped data.

### Best Practices

1. **Start Small**: Test with 5-10 profiles first
2. **Use Proxy**: Consider using Apify proxy to avoid detection
3. **Rotate Cookies**: Use different accounts if scraping large volumes
4. **Respect Privacy**: Only use data ethically and legally
5. **Fresh Cookies**: Cookies expire - update them regularly

### Limitations

- Requires valid LinkedIn session cookies
- Can only access public profile information
- Cannot scrape profiles you don't have permission to view
- LinkedIn may rate-limit or block suspicious activity
- Skills, education, certifications require additional API calls (coming in v2.0)

## Troubleshooting 🔧

### "Failed to fetch LinkedIn data"
- Your cookies may have expired - get fresh cookies
- LinkedIn may have detected scraping activity
- Profile may be private or restricted

### "Could not extract FSD profile ID"
- Profile username may be incorrect
- Profile may not exist
- Cookies may be invalid

### No email or websites returned
- These fields are only available if the user has made them public
- Check the profile manually to verify visibility

## Support 📧

Need help? Found a bug? Have a feature request?

- Open an issue on GitHub
- Contact us through Apify support
- Check the Apify community forum

## Changelog 📅

### v1.0.0 (February 2024)
- Initial release
- Extract basic profile information
- Extract work experience with full details
- Contact information scraping
- Company logo URLs

## Roadmap 🗺️

Planned features for future versions:
- Education history
- Skills and endorsements
- Certifications and licenses
- Recommendations
- Publications and patents
- Volunteer experience
- Languages
- Honors and awards

## FAQ ❓

**Q: Is this legal?**
A: Web scraping exists in a legal gray area. LinkedIn's ToS prohibits automated scraping, but public data scraping may be protected in some jurisdictions. Consult a lawyer for your specific use case.

**Q: Can I scrape private profiles?**
A: No, you can only scrape profiles that are publicly visible with your LinkedIn account.

**Q: How do I get more data like education and skills?**
A: These features are coming in version 2.0. Subscribe to updates!

**Q: Can I use this for commercial purposes?**
A: Check your local laws and LinkedIn's ToS. We don't provide legal advice.

**Q: Will this get my LinkedIn account banned?**
A: There's always a risk with scraping. Use responsibly, don't scrape aggressively, and consider using dedicated accounts.

## License 📄

This actor is provided as-is without warranty. Use at your own risk.

---

**Developed with ❤️ for the Apify community**

*Last updated: February 2024*
