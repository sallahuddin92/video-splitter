# Deployment Guide: Netlify (Frontend) + Render (Backend)

## Overview
- **Frontend**: Static HTML → Netlify (Free)
- **Backend**: FastAPI Python → Render (Free tier)

---

## Part 1: Deploy Backend to Render

### Step 1: Push Code to GitHub
```bash
cd /Users/muhammadsallahuddinhamzah/Desktop/downloader
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/video-splitter.git
git push -u origin main
```

### Step 2: Create Render Account
1. Go to [render.com](https://render.com)
2. Sign up with GitHub

### Step 3: Create Web Service
1. Click **New** → **Web Service**
2. Connect your GitHub repository
3. Configure:
   - **Name**: `video-splitter-api`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
4. Click **Create Web Service**

### Step 4: Add YouTube Cookies (Recommended to fix errors)
If you see "Sign in to confirm you're not a bot" errors:

1. **Get Cookies**:
   - Install "Get cookies.txt LOCALLY" extension for Chrome/Edge.
   - Go to YouTube.com and log in.
   - Click the extension to download `cookies.txt`.
   - Open the file and copy the **entire content**.

2. **Add to Render**:
   - Go to your Render Dashboard > **Environment**.
   - Add new variable:
     - **Key**: `YOUTUBE_COOKIES`
     - **Value**: (Paste the entire text content from cookies.txt)
   - Click **Save Changes**. Render will redeploy.

### Step 5: Wait for Deployment
- Render will build and deploy your app
- Copy your URL: `https://video-splitter-api.onrender.com`

> ⚠️ **Note**: Render free tier sleeps after 15 min of inactivity. First request may take ~30 seconds.

---

## Part 2: Deploy Frontend to Netlify

### Step 1: Update API URL in HTML
Before deploying, update `ReelCutter.html` (or `frontend/index.html`):

```javascript
// Change this line:
const API_BASE = "http://127.0.0.1:8000";

// To your Render URL:
const API_BASE = "https://video-splitter-api.onrender.com";
```

### Step 2: Deploy to Netlify
1. Go to [app.netlify.com](https://app.netlify.com)
2. Drag the `frontend` folder onto the page
3. Done! Get your URL.

---

## Part 3: Update CORS (Important!)

After deploying frontend, update `main.py` to allow your Netlify domain:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://your-site.netlify.app",  # Add your Netlify URL
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```
