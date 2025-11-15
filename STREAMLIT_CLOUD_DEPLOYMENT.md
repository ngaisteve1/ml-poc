# Streamlit Cloud Deployment Guide

**Date:** November 15, 2025  
**Status:** Ready for Deployment  
**Expected Time:** 5-10 minutes  

---

## 🚀 Step-by-Step Deployment to Streamlit Cloud

### Prerequisites
- ✅ GitHub account with access to this repo
- ✅ All code committed and pushed to `ml-poc` branch
- ✅ `config/requirements.txt` updated with all dependencies
- ✅ `.streamlit/config.toml` configured

### Step 1: Create Streamlit Cloud Account (2 minutes)

1. Go to: https://streamlit.io/cloud
2. Click **"Sign in"** → **"Sign up with GitHub"**
3. Authorize Streamlit to access your GitHub repositories
4. Verify your email

**Result:** You have a Streamlit Cloud account

---

### Step 2: Connect Your Repository (2 minutes)

1. On Streamlit Cloud dashboard, click **"New app"**
2. Select:
   - **Repository:** `Navoo-Product-Development-Navoo.SmartArchive`
   - **Branch:** `ml-poc`
   - **Main file path:** `src/ui/streamlit_app.py`
3. Click **"Deploy"**

**The app will:**
- Install dependencies from `config/requirements.txt`
- Run `src/ui/streamlit_app.py`
- Create a public URL (something like: `https://ml-poc-smartarchive.streamlit.app`)

---

### Step 3: Wait for Deployment (3-5 minutes)

Watch the deployment logs:
```
Installing dependencies... ✓
Setting up environment... ✓
Starting app... ✓
App is live! 🎉
```

**Status:** Available at the provided URL

---

### Step 4: Verify Deployment (2 minutes)

Once live:

1. **Visit your app URL** (Streamlit will provide it)
2. **Check each tab works:**
   - ✅ Tab 1: Active Alerts (shows mock alerts)
   - ✅ Tab 2: Prediction History (shows chart)
   - ✅ Tab 3: Drift Detection (shows statistics)
   - ✅ Tab 4: Performance Metrics (shows dashboard)
   - ✅ Tab 5: Settings (shows sliders)

3. **Test interactions:**
   - Change date range filters
   - Adjust threshold sliders
   - Hover over charts to see values

**Expected:** All tabs load without errors

---

### Step 5: Share Your App

**Get the URL:**
```
https://[your-app-name].streamlit.app
```

**Share with stakeholders:**
- Email the link
- Add to documentation
- Include in presentations
- Works on mobile and desktop

---

## 🔧 Troubleshooting

### Issue: "Module not found" error

**Solution:**
1. Check `config/requirements.txt` has all imports
2. Add missing packages: `scipy`, `pytz`, etc.
3. Commit and push changes
4. Streamlit auto-redeploys

### Issue: "streamlit_app.py not found"

**Solution:**
1. Verify file exists at: `src/ui/streamlit_app.py`
2. Check the "Main file path" setting in Streamlit Cloud
3. Correct path if needed, redeploy

### Issue: "Mock data not loading"

**Solution:**
1. Ensure `mock_data.py` exists in `src/ui/`
2. All imports in `streamlit_app.py` are relative imports
3. Test locally: `streamlit run src/ui/streamlit_app.py`

### Issue: "App starts but no data shows"

**Solution:**
1. Check browser console (F12) for JS errors
2. Check Streamlit logs for Python errors
3. Mock data might not be loading - verify `mock_data.py`

---

## 📊 What Gets Deployed

```
Repository Structure:
├── src/
│   ├── ui/
│   │   ├── streamlit_app.py          ← Main app
│   │   ├── mock_data.py              ← Demo data
│   │   └── __init__.py
│   ├── monitoring/
│   │   ├── predictions_db.py          ← Database layer
│   │   ├── drift_detector.py          ← Drift detection
│   │   └── alerts.py                  ← Alert management
│   └── ...
├── config/
│   └── requirements.txt               ← Dependencies
├── .streamlit/
│   └── config.toml                    ← Streamlit settings
└── monitoring.db                       ← Data file (if present)

Streamlit Cloud runs:
1. pip install -r config/requirements.txt
2. streamlit run src/ui/streamlit_app.py
3. Creates public URL
4. Auto-reloads on code push
```

---

## 🔄 Continuous Deployment (Auto-Update)

**Great news:** Streamlit Cloud auto-redeploys when you push to GitHub!

**How it works:**
1. Make code changes locally
2. Commit and push to `ml-poc` branch
3. Streamlit detects the push
4. Automatically rebuilds and deploys
5. Your live app updates (30-60 seconds)

**Example workflow:**
```bash
git add -A
git commit -m "Update dashboard styling"
git push origin ml-poc
# -> Streamlit auto-deploys within 1 minute
```

---

## 📋 Deployment Checklist

- [ ] GitHub account created and repo accessible
- [ ] All code committed and pushed to `ml-poc`
- [ ] `config/requirements.txt` updated with all packages
- [ ] `.streamlit/config.toml` created
- [ ] Streamlit Cloud account created
- [ ] Repository connected to Streamlit Cloud
- [ ] Deployment completed (no errors)
- [ ] Live URL provided by Streamlit
- [ ] All 5 tabs load and display data
- [ ] Interactions work (filters, sliders, hover)
- [ ] URL shared with stakeholders

---

## 🎯 Your Live App URL

Once deployed, your app will be available at:
```
https://[your-username]-[repo-name]-[branch].streamlit.app
```

Example:
```
https://arvato-systems-navoo-smartarchive-ml-poc.streamlit.app
```

**Share this link** with stakeholders to show them the live dashboard! 🎉

---

## 📞 Support

### Streamlit Cloud Docs
- https://docs.streamlit.io/streamlit-cloud/get-started

### Common Issues
- Check deployment logs for error messages
- Verify all imports are installed
- Test locally first: `streamlit run src/ui/streamlit_app.py`
- Check network for CORS issues (if calling APIs)

### Questions?
- Streamlit Cloud supports push-to-deploy automatically
- No additional configuration needed for basic apps
- For advanced features (secrets, resources), see docs

---

**Estimated Total Time: 10-15 minutes from start to live app** ⏱️

Let's deploy! 🚀
