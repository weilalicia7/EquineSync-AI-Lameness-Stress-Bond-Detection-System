# EquineSync Deployment Guide

## Quick Deployment to Render.com (FREE)

Perfect for hackathon judging - deploys in under 5 minutes!

### Step 1: Push Code to GitHub (Already Done ✅)
Your code is at: https://github.com/weilalicia7/EquineSync-AI-Lameness-Stress-Bond-Detection-System

### Step 2: Deploy to Render.com

1. **Go to Render.com**
   - Visit: https://render.com
   - Click "Get Started for Free"
   - Sign up with your GitHub account (no credit card required)

2. **Create New Web Service**
   - Click "New +" button
   - Select "Web Service"
   - Click "Connect account" to link your GitHub
   - Select repository: `EquineSync-AI-Lameness-Stress-Bond-Detection-System`

3. **Configure Service**
   - **Name**: `equinesync-demo` (or any name you prefer)
   - **Region**: Choose closest to judges (e.g., Oregon - US West)
   - **Branch**: `main`
   - **Root Directory**: Leave blank
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python src/demo_data_loader.py`
   - **Instance Type**: `Free` (select the free tier)

4. **Environment Variables** (Optional)
   - Click "Advanced"
   - Add if needed: `PYTHON_VERSION = 3.9.0`

5. **Deploy**
   - Click "Create Web Service"
   - Wait 3-5 minutes for deployment
   - Your app will be live at: `https://equinesync-demo.onrender.com`

### Step 3: Test Your Deployment

Once deployed, your public URL will be:
```
https://equinesync-demo.onrender.com
```

Test these endpoints:
- **Main Dashboard**: https://equinesync-demo.onrender.com/
- **Demo Page**: https://equinesync-demo.onrender.com/demo.html
- **API Status**: https://equinesync-demo.onrender.com/api/status
- **Gait Analysis**: https://equinesync-demo.onrender.com/api/gait/analysis

### Step 4: Submit to Hackathon

Use this URL for judging:
```
https://equinesync-demo.onrender.com
```

---

## Alternative: Railway.app Deployment

If Render doesn't work, try Railway.app (also free):

1. Visit https://railway.app
2. Sign in with GitHub
3. Click "New Project"
4. Select "Deploy from GitHub repo"
5. Choose your repository
6. Railway auto-detects Python and deploys
7. Get your URL from the deployment page

---

## Alternative: Vercel Deployment (Static Only)

For frontend-only deployment:

1. Visit https://vercel.com
2. Import your GitHub repository
3. Configure:
   - Framework Preset: Other
   - Build Command: (leave empty)
   - Output Directory: `.`
4. Deploy

Note: Vercel is for static files only. API endpoints won't work unless you set up serverless functions.

---

## Local Testing (Already Working)

If judges want to run locally:

```bash
# Terminal 1 - API Server
python src/demo_data_loader.py
# Runs on http://localhost:8000

# Terminal 2 - Static Server (optional)
python serve.py
# Runs on http://localhost:5180
```

---

## Troubleshooting

### Issue: "Demo session not found"
**Solution**: The demo_data folder is included in your repository. If missing, run:
```bash
python src/data_processor.py
```

### Issue: "Module not found"
**Solution**: Ensure all dependencies are in requirements.txt (already configured)

### Issue: "Port already in use"
**Solution**: Render automatically assigns ports via PORT environment variable (already configured)

---

## What Judges Will See

When judges visit your deployed URL, they'll see:

1. **Live Demo Dashboard** - Real-time horse gait monitoring
2. **Symmetry Charts** - 4-leg gait analysis with Chart.js
3. **HRV Monitoring** - Heart rate variability trends
4. **Bond Score** - Horse-rider emotional connection
5. **Session Reports** - Downloadable clinical reports
6. **Lameness Alerts** - Real-time detection (triggers at 60s mark)

All powered by authentic equine IMU data from the "Horsing Around" dataset!

---

## Support

- Render Docs: https://render.com/docs
- Railway Docs: https://docs.railway.app
- GitHub Repo: https://github.com/weilalicia7/EquineSync-AI-Lameness-Stress-Bond-Detection-System
