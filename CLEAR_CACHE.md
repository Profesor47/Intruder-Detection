# Browser Cache Clearing Guide

The error you're seeing is from a **stale browser cache** showing old code. Follow these steps to fix it:

## **Option 1: Hard Refresh (Quickest)**

**Windows/Linux:**
- Press `Ctrl + Shift + R` while on the website

**Mac:**
- Press `Cmd + Shift + R` while on the website

This forces your browser to download fresh JavaScript instead of using cached files.

---

## **Option 2: Clear Browser Cache Completely**

### **Chrome/Brave:**
1. Press `Ctrl + Shift + Delete` (Windows) or `Cmd + Shift + Delete` (Mac)
2. Select "All time" for time range
3. Check "Cookies and other site data" and "Cached images and files"
4. Click "Clear data"
5. Refresh the page

### **Firefox:**
1. Press `Ctrl + Shift + Delete` (Windows) or `Cmd + Shift + Delete` (Mac)
2. Select "Everything" for time range
3. Click "Clear Now"
4. Refresh the page

### **Safari:**
1. Go to Safari → Preferences
2. Click "Privacy" tab
3. Click "Manage Website Data"
4. Select `localhost:3000`
5. Click "Remove"
6. Refresh the page

---

## **Option 3: Restart Everything**

If hard refresh doesn't work, stop and restart both servers:

1. **Stop the Next.js frontend:**
   - Press `Ctrl + C` in the terminal running `npm run dev` or `pnpm dev`

2. **Stop the FastAPI backend:**
   - Press `Ctrl + C` in the terminal running the Python backend

3. **Clear Node cache:**
   ```bash
   rm -rf .next
   ```

4. **Restart the backend:**
   ```bash
   python -m uvicorn backend.app:app --reload --host 0.0.0.0 --port 8000
   ```

5. **Restart the frontend:**
   ```bash
   npm run dev
   # or
   pnpm dev
   ```

6. **Hard refresh** your browser: `Ctrl + Shift + R` or `Cmd + Shift + R`

---

## **Verify Everything is Working**

After clearing cache, check:

1. **Backend API Docs:**
   - Visit `http://localhost:8000/docs`
   - You should see all endpoints listed

2. **Test Endpoints:**
   - Visit `http://localhost:8000/api/health` → should show `{"status":"healthy"}`
   - Visit `http://localhost:8000/api/alerts?limit=10` → should show alert data
   - Visit `http://localhost:8000/api/detections?limit=50` → should show detection data

3. **Frontend:**
   - Visit `http://localhost:3000`
   - Browser console should NOT show "Failed to fetch" errors
   - Alert Timeline should display data

---

## **If You Still Get Errors**

1. **Check backend is running:**
   ```bash
   curl http://localhost:8000/api/health
   ```
   Should return: `{"status":"healthy"}`

2. **Check frontend can access backend:**
   ```bash
   curl http://localhost:3000/api/health
   ```
   Should return: `{"status":"healthy"}`

3. **Check browser console for actual error messages:**
   - Press `F12` to open Developer Tools
   - Go to "Console" tab
   - Look for the actual error details

