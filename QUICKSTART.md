# Quick Start Guide

## 🚀 Get Started in 5 Minutes

### Step 1: Get LinkedIn Cookies (2 minutes)

1. Open Chrome/Firefox and log into LinkedIn
2. Press `F12` to open Developer Tools
3. Go to `Application` tab (Chrome) or `Storage` tab (Firefox)
4. Click `Cookies` → `https://www.linkedin.com`
5. Copy these cookie values:
   - `li_at` (most important)
   - `JSESSIONID`
   - Copy all cookies for best results

**Cookie format:**
```
li_at=YOUR_LI_AT_VALUE; JSESSIONID=ajax:1234567; bcookie=v=2&abc...
```

### Step 2: Deploy to Apify (2 minutes)

**Via Apify Console:**
1. Go to https://console.apify.com
2. Click "Create new actor"
3. Choose "Empty Python actor"
4. Upload these files:
   - `main.py`
   - `requirements.txt`
   - `Dockerfile`
   - `.actor/actor.json`
   - `.actor/input_schema.json`
   - `README.md`
5. Click "Build" and wait 2-3 minutes

**Via CLI:**
```bash
npm install -g apify-cli
apify login
apify push
```

### Step 3: Test It (1 minute)

Go to your actor's Console tab and paste:

```json
{
  "profiles": [
    "williamhgates",
    "satyanadella"
  ],
  "cookies": "YOUR_COOKIES_HERE"
}
```

Click "Start" and watch the magic happen! ✨

### Step 4: Check Results

- Go to "Dataset" tab to see scraped data
- Export as JSON, CSV, or Excel
- Use the data in your application

## 💰 Monetization Setup

### Publish to Apify Store

1. Go to actor settings
2. Set visibility to "Public"
3. Add store listing:
   - Upload icon (512x512 PNG)
   - Add description (use README.md)
   - Set categories: Business, Marketing, Lead Generation
   - Add tags: linkedin, scraper, leads
4. Set pricing:
   - **Freemium**: 100 profiles free, then $19/month
   - **Pay-per-use**: $0.01 per profile
   - **Subscription**: $29/month unlimited
5. Submit for review

### Expected Earnings

**Conservative estimate:**
- 50 users at $19/month = $950/month
- 5 enterprise at $99/month = $495/month
- **Total: ~$1,400/month**

**Optimistic estimate:**
- 200 users at $19/month = $3,800/month
- 20 enterprise at $99/month = $1,980/month
- **Total: ~$5,700/month**

## 🎯 Marketing Checklist

- [ ] Launch on ProductHunt
- [ ] Post on Reddit (r/datascience, r/learnpython)
- [ ] Write Medium article
- [ ] Create YouTube demo
- [ ] Tweet about launch
- [ ] Join Apify Discord and share
- [ ] Update LinkedIn (carefully!)
- [ ] Submit to Indie Hackers

## 📊 Success Metrics to Track

Week 1:
- [ ] 10 users
- [ ] 5-star review
- [ ] $0-50 revenue

Month 1:
- [ ] 50 users
- [ ] 5+ reviews
- [ ] $200-500 revenue

Month 3:
- [ ] 200 users
- [ ] 4.5+ star rating
- [ ] $1,000+ revenue

## ⚠️ Important Notes

### Legal
- Add ToS and Privacy Policy links
- Include GDPR disclaimer
- Warn about LinkedIn ToS
- Recommend ethical use only

### Technical
- Monitor error rates
- Update regex if LinkedIn changes
- Respond to support quickly
- Add features based on feedback

## 🆘 Troubleshooting

**Build fails?**
- Check Python version in Dockerfile (should be 3.11)
- Verify requirements.txt syntax

**Actor fails?**
- Cookies expired - get fresh ones
- Profile doesn't exist - check username
- Rate limited - add delays

**No sales?**
- Improve documentation
- Add demo video
- Lower price temporarily
- Promote more actively

## 🔥 Pro Tips

1. **Start free tier** - Get users, then monetize
2. **Respond fast** - Best support = best reviews
3. **Add features** - Education, skills, etc.
4. **Bundle deals** - Offer with other scrapers
5. **Affiliate program** - 20% commission for referrals

## 📧 Need Help?

- Apify Discord: https://discord.gg/jyEM2PRvMU
- Apify Docs: https://docs.apify.com
- Email support: support@apify.com

## What's Next?

Once deployed:
1. ✅ Test with 10-20 profiles
2. ✅ Get 1-2 beta users for feedback
3. ✅ Publish to store
4. ✅ Launch marketing campaign
5. ✅ Monitor and iterate

**You're ready to make money! 🎉**

Good luck! 🚀
