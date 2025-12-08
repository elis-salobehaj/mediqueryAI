# API Configuration - Single Source of Truth

## Overview
The frontend API URL is now managed through a single source of truth using Vite's environment variable system.

## Configuration Hierarchy

### 1. Local Development (`npm run dev`)
**Source:** `frontend/.env`
```env
VITE_API_URL=http://localhost:8000
```

### 2. Docker Build
**Source:** `docker-compose.yml` → `frontend/Dockerfile`
```yaml
frontend:
  build:
    args:
      VITE_API_URL: http://localhost:8000
```

### 3. Code Usage
**Source:** `frontend/src/config/api.ts`
```typescript
export const API_CONFIG = {
  BASE_URL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
};
```

## Files Modified

1. **`frontend/src/config/api.ts`** (NEW)
   - Central API configuration module
   - Exports `API_CONFIG` and `getApiUrl()` helper

2. **`frontend/src/App.tsx`**
   - Updated to use `getApiUrl('/history')`
   - Removed hardcoded URL

3. **`frontend/src/components/ChatBox.tsx`**
   - Updated to use `getApiUrl('/query')`
   - Removed hardcoded URL

4. **`frontend/.env`** (NEW)
   - Local development environment variables
   - Sets `VITE_API_URL=http://localhost:8000`

5. **`frontend/.env.example`** (NEW)
   - Template for environment variables
   - Documentation for developers

6. **`frontend/Dockerfile`**
   - Added `ARG VITE_API_URL`
   - Passes build arg to environment

7. **`docker-compose.yml`**
   - Added `build.args.VITE_API_URL`
   - Single source for Docker deployments

## Usage Examples

### In Code
```typescript
import { getApiUrl } from './config/api';

// Instead of: 'http://localhost:8000/query'
const url = getApiUrl('/query');

// Or access directly
import { API_CONFIG } from './config/api';
console.log(API_CONFIG.BASE_URL);
```

### Changing API URL

**For Local Development:**
Edit `frontend/.env`:
```env
VITE_API_URL=http://localhost:3001
```

**For Docker:**
Edit `docker-compose.yml`:
```yaml
frontend:
  build:
    args:
      VITE_API_URL: http://backend:8000
```

## Benefits

1. ✅ **Single Source of Truth** - API URL defined once
2. ✅ **Environment-Specific** - Different URLs for dev/prod
3. ✅ **Type-Safe** - TypeScript configuration module
4. ✅ **Easy to Change** - Update in one place
5. ✅ **Docker-Friendly** - Build args for containerization
6. ✅ **Developer-Friendly** - Clear .env.example template

## Migration Complete

All hardcoded `http://localhost:8000` references have been replaced with the centralized configuration system.
