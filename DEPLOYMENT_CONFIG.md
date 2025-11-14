# Deployment Configuration Guide

## Dynamic URL Configuration

This application is configured to **automatically detect** the correct backend URL based on the environment, eliminating the need for manual configuration changes during deployment.

## How It Works

### Frontend Auto-Detection

The frontend (`/app/frontend/src/App.js`) automatically determines the backend URL using this logic:

1. **Environment Variable Check**: 
   - If `REACT_APP_BACKEND_URL` is set in `.env`, it uses that value
   - Useful for local development with custom URLs

2. **Localhost Detection** (Development):
   - If hostname is `localhost` or `127.0.0.1`
   - Uses: `http://localhost:8001`

3. **Production Auto-Detection**:
   - Uses the current domain the app is served from
   - If deployed at `www.kawalecranes.com`, it automatically uses `https://www.kawalecranes.com`
   - If deployed at `preview.example.com`, it automatically uses `https://preview.example.com`

### Backend Configuration

The backend uses environment variables from `/app/backend/.env`:

- `MONGO_URL`: MongoDB connection string
- `DB_NAME`: Database name
- `CORS_ORIGINS`: Allowed origins for CORS (set to "*" for all)
- `SECRET_KEY`: JWT authentication secret

These are automatically loaded and don't need manual changes for deployment.

## Deployment Checklist

When deploying to a new environment:

✅ **No manual changes needed!** The app auto-configures.

### Optional: Environment-Specific Overrides

If you need to override the auto-detection:

**Frontend** (`/app/frontend/.env`):
```env
REACT_APP_BACKEND_URL=https://custom-backend-url.com
```

**Backend** (`/app/backend/.env`):
```env
MONGO_URL=mongodb://your-mongo-host:27017
DB_NAME=your_database_name
```

## Verification

After deployment, check browser console:

```
🔗 Backend URL Configuration: https://www.kawalecranes.com
🔗 API Endpoint: https://www.kawalecranes.com/api
```

If these match your deployment domain, everything is configured correctly!

## Supported Environments

- ✅ Local Development (`localhost:3000` → `localhost:8001`)
- ✅ Preview Deployments (auto-detects preview URL)
- ✅ Production Deployments (auto-detects production URL)
- ✅ Custom Domains (auto-detects custom domain)

## Database Seeding

On first deployment to a new environment:

1. Backend automatically seeds database with Excel data from `/app/backend/seed_data.xlsx`
2. Checks if data already exists to prevent duplicates
3. Logs seeding status: `[SEED] Database seeding complete!`

## Troubleshooting

**Issue**: Data not showing after deployment
**Solution**: Check that frontend URL matches deployment domain

**Issue**: CORS errors
**Solution**: Verify `CORS_ORIGINS` in backend `.env`

**Issue**: Database connection failed
**Solution**: Verify `MONGO_URL` and `DB_NAME` in backend `.env`

## Files Configuration Summary

| File | Purpose | Auto-Configured |
|------|---------|-----------------|
| `/app/frontend/.env` | Frontend config | ✅ Yes (auto-detects) |
| `/app/backend/.env` | Backend config | ✅ Yes (uses env vars) |
| `/app/frontend/src/App.js` | Dynamic URL logic | ✅ Yes (built-in) |
| `/app/backend/server.py` | API endpoints | ✅ Yes (uses env vars) |

## Result

🎉 **Zero-configuration deployment** - Deploy anywhere and it just works!
