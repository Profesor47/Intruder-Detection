# GUARDZILLA Backend Setup & Running

## Prerequisites

Make sure you have Python 3.9+ installed.

## Installation

1. Navigate to the backend directory:
```bash
cd backend
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

Or if using UV:
```bash
uv pip install -r requirements.txt
```

## Running the Backend

Start the FastAPI server:

```bash
python -m uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

You should see output like:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete
```

## Testing the Backend

Once running, you can test endpoints:

1. **Health Check** (should always work):
   ```
   http://localhost:8000/api/health
   ```

2. **System Status**:
   ```
   http://localhost:8000/api/status
   ```

3. **API Documentation** (interactive):
   ```
   http://localhost:8000/docs
   ```

4. **Known Faces**:
   ```
   http://localhost:8000/api/known-faces
   ```

## Frontend & Backend Communication

The Next.js frontend (port 3000) communicates with the FastAPI backend (port 8000) through:
- **Next.js rewrites** proxy all `/api/*` requests to `http://localhost:8000/api/*`

This solves CORS issues and allows the frontend to call the backend seamlessly.

## Troubleshooting

If you get "Failed to fetch" errors:

1. **Make sure backend is running** on port 8000
2. **Hard refresh the browser** (Ctrl+Shift+R or Cmd+Shift+R)
3. **Check browser console** for detailed error messages
4. **Verify endpoints** at http://localhost:8000/docs
