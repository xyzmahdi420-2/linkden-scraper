# 🚀 UPDATED DEPLOYMENT GUIDE - Fixed Structure

## ✅ What Changed

The actor now uses a proper Python package structure:

```
linkedin-scraper/
├── requirements.txt
├── Dockerfile
├── .actor/
│   ├── actor.json
│   └── input_schema.json
├── README.md
└── src/                    ← NEW DIRECTORY
    ├── __init__.py        ← NEW FILE
    ├── __main__.py        ← NEW FILE (entry point)
    └── main.py            ← Moved here
```

## 📦 Files to Upload to Apify

### Method 1: Via Apify Console

1. **Go to your actor** → Source tab
2. **Delete all existing files**
3. **Upload in this order:**

**Root files:**
- `requirements.txt`
- `Dockerfile`
- `README.md`

**Create `.actor` folder and upload:**
- `.actor/actor.json`
- `.actor/input_schema.json`

**Create `src` folder and upload:**
- `src/__init__.py`
- `src/__main__.py`
- `src/main.py`

4. **Build** and it should work!

### Method 2: Via GitHub

Your repository structure should be:

```
your-repo/
├── requirements.txt
├── Dockerfile
├── README.md
├── .actor/
│   ├── actor.json
│   └── input_schema.json
└── src/
    ├── __init__.py
    ├── __main__.py
    └── main.py
```

Commit and push, then Apify will auto-build.

## 📝 File Contents

### requirements.txt
```
apify>=2.0.0,<3.0.0
requests>=2.31.0
beautifulsoup4>=4.12.0
lxml>=4.9.0
```

### Dockerfile
```dockerfile
FROM apify/actor-python:3.11

# Copy requirements and install dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src ./src

# Run the actor
CMD ["python3", "-m", "src"]
```

### src/__init__.py
```python
"""LinkedIn Profile Scraper package."""
```

### src/__main__.py
```python
"""Apify Actor entry point."""
import asyncio
from src.main import main

if __name__ == '__main__':
    asyncio.run(main())
```

### src/main.py
(Use the main.py file I provided - it's already in the outputs folder)

## 🧪 Testing

After build succeeds, test with:

```json
{
  "profiles": ["williamhgates"],
  "cookies": "YOUR_LINKEDIN_COOKIES"
}
```

## ✅ Build Should Show

```
Step 1/4 : FROM apify/actor-python:3.11
Step 2/4 : COPY requirements.txt ./
Step 3/4 : RUN pip install --no-cache-dir -r requirements.txt
Step 4/4 : COPY src ./src
Step 5/4 : CMD python3 -m src
Successfully built
```

## 🎯 Why This Structure?

This is the **standard Python package structure** that works reliably with Apify:

- `src/` = source package directory
- `src/__init__.py` = makes src a Python package
- `src/__main__.py` = entry point when running `python -m src`
- `src/main.py` = actual scraper code

This avoids all the "__main__" module specification errors!

## 🐛 Troubleshooting

### Error: "No module named 'src'"
**Fix**: Make sure you uploaded the `src` folder with all 3 files inside

### Error: "cannot import name 'main'"
**Fix**: Make sure `src/main.py` exists and contains the `async def main()` function

### Error: "Input schema is not valid"
**Fix**: Use the fixed `input_schema.json` where `placeholderValue` is a string

## 🚀 Quick Commands (if using CLI)

```bash
# Structure your directory
mkdir -p src .actor

# Move files
mv main.py src/
# Create the other src files

# Push to Apify
apify push

# Build
apify build
```

---

**This structure will work!** It's the standard way Apify Python actors are built. 🎉
