# Google Cloud Console Setup Guide

Complete guide to setting up Google Calendar API access for your calendar app.

---

## Step 1: Access Google Cloud Console

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Sign in with your Google account
3. Select your project OR create a new one:
   - Click the project dropdown at the top
   - Click "New Project"
   - Name it: "Calendar App" (or whatever you prefer)
   - Click "Create"

---

## Step 2: Enable Google Calendar API

1. In the left sidebar, go to **"APIs & Services"** → **"Library"**
2. Search for **"Google Calendar API"**
3. Click on it
4. Click the **"Enable"** button
5. Wait for it to enable (takes a few seconds)

✅ This allows your app to access the Google Calendar API

---

## Step 3: Configure OAuth Consent Screen

This is what users see when they authorize your app.

1. Go to **"APIs & Services"** → **"OAuth consent screen"**
2. Choose **"External"** (unless you have Google Workspace)
3. Click **"Create"**

### **App Information:**
- **App name**: `Calendar App` (or your app name)
- **User support email**: Your email address
- **App logo**: (optional, can skip)

### **App domain:**
- **Application home page**: `http://localhost:3000` (your frontend)
- **Privacy policy**: (optional for testing, can skip)
- **Terms of service**: (optional for testing, can skip)

### **Developer contact information:**
- **Email addresses**: Your email address

4. Click **"Save and Continue"**

---

## Step 4: Add Scopes

Scopes define what permissions your app needs.

1. Click **"Add or Remove Scopes"**
2. Filter/search for: **"Google Calendar API"**
3. Select these scopes:

```
✅ .../auth/calendar.readonly     (Read calendar events)
✅ .../auth/calendar.events        (Read/write calendar events)
✅ .../auth/calendar               (Full calendar access)
```

**Recommended**: Select `.../auth/calendar` for full access (read + write)

4. Click **"Update"**
5. Click **"Save and Continue"**

---

## Step 5: Add Test Users (Development Only)

While your app is in testing mode, only specific users can authorize it.

1. Click **"Add Users"**
2. Add email addresses of people who will test (including yourself):
   ```
   your-email@gmail.com
   tester@gmail.com
   ```
3. Click **"Add"**
4. Click **"Save and Continue"**

**Note**: In production, you'll submit for verification to allow any Google user.

---

## Step 6: Create OAuth 2.0 Credentials

This is where you get the CLIENT_ID and CLIENT_SECRET.

1. Go to **"APIs & Services"** → **"Credentials"**
2. Click **"Create Credentials"** → **"OAuth 2.0 Client ID"**

### **Application type:**
- Select: **"Web application"**

### **Name:**
- Enter: `Calendar App Backend` (or any name)

### **Authorized JavaScript origins** (Optional):
```
http://localhost:3000
http://localhost:8000
```

### **Authorized redirect URIs** (IMPORTANT!):
Add these EXACT URLs:
```
http://localhost:8000/oauth/google/callback
http://localhost:3000/api/auth/callback/google
```

⚠️ **These must match EXACTLY** - no trailing slashes, correct port numbers

3. Click **"Create"**

---

## Step 7: Copy Your Credentials

A popup will appear with your credentials:

```
Client ID:
123456789-abcdefghijklmnop.apps.googleusercontent.com

Client Secret:
GOCSPX-your_secret_here
```

### **Add to your `.env` file:**

```bash
# backend/.env
GOOGLE_CLIENT_ID=123456789-abcdefghijklmnop.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-your_secret_here
GOOGLE_REDIRECT_URI=http://localhost:8000/oauth/google/callback
```

⚠️ **Keep these secret!** Never commit to Git.

---

## Step 8: Update .gitignore

Make sure your `.env` file is not tracked:

```bash
# .gitignore (already should have this)
.env
*.env
.env.local
```

---

## Verification Checklist

Before testing, verify:

- ✅ Google Calendar API is **enabled**
- ✅ OAuth consent screen is **configured**
- ✅ Scopes include **calendar access**
- ✅ Your email is added as **test user**
- ✅ OAuth client is created as **Web application**
- ✅ Redirect URI is **exactly**: `http://localhost:8000/oauth/google/callback`
- ✅ CLIENT_ID and CLIENT_SECRET are in **`.env`** file
- ✅ `.env` is in **`.gitignore`**

---

## Testing the Setup

### 1. Start your backend:
```bash
cd backend
uvicorn app.main:app --reload
```

### 2. Test the authorization URL:
```bash
# This should return a 501 with instructions (not implemented yet)
curl http://localhost:8000/oauth/google/authorize
```

### 3. Check API documentation:
Visit: http://localhost:8000/docs

Look for these endpoints:
- GET `/oauth/google/authorize`
- GET `/oauth/google/callback`
- POST `/oauth/google/disconnect`
- GET `/oauth/google/status`

---

## Common Issues & Solutions

### Issue: "Redirect URI mismatch"
**Solution**:
- Check that redirect URI in Google Console EXACTLY matches your `.env`
- No trailing slash
- Correct port number (8000 for backend)
- Use `http://` not `https://` for localhost

### Issue: "Access blocked: This app's request is invalid"
**Solution**:
- Make sure you added your email as a test user
- Check that all required scopes are added
- Verify OAuth consent screen is configured

### Issue: "The OAuth client was not found"
**Solution**:
- Verify GOOGLE_CLIENT_ID is correct in `.env`
- Check you're using the right Google Cloud project
- Make sure OAuth client is created (not just API key)

### Issue: "Invalid client secret"
**Solution**:
- Copy the client secret again from Google Console
- Make sure there are no extra spaces in `.env`
- Try regenerating the secret

---

## Production Deployment

When deploying to production:

### 1. Update Redirect URIs:
Add your production domain:
```
https://yourdomain.com/oauth/google/callback
```

### 2. Update Environment Variables:
```bash
GOOGLE_REDIRECT_URI=https://yourdomain.com/oauth/google/callback
```

### 3. Submit for Verification:
- In OAuth consent screen, click "Publish App"
- Google will review your app
- Provides access to all Google users (not just test users)

---

## Security Best Practices

1. **Never commit credentials**:
   - Keep `.env` in `.gitignore`
   - Use environment variables in production

2. **Rotate secrets periodically**:
   - Generate new client secret every 6-12 months
   - Update `.env` file

3. **Use HTTPS in production**:
   - Never use `http://` for production
   - Always use `https://` for redirect URIs

4. **Limit scopes**:
   - Only request calendar permissions you need
   - Don't request broader access than necessary

5. **Validate state parameter**:
   - Prevents CSRF attacks
   - Implement in OAuth callback handler

---

## Next Steps

Once setup is complete:

1. ✅ Test the OAuth flow
2. ✅ Implement token refresh logic
3. ✅ Test calendar sync
4. ✅ Test event creation/modification
5. ✅ Add error handling
6. ✅ Prepare for production deployment

---

## Resources

- [Google Calendar API Documentation](https://developers.google.com/calendar/api/guides/overview)
- [OAuth 2.0 for Web Server Applications](https://developers.google.com/identity/protocols/oauth2/web-server)
- [Google API Python Client](https://github.com/googleapis/google-api-python-client)
- [OAuth 2.0 Scopes for Google APIs](https://developers.google.com/identity/protocols/oauth2/scopes#calendar)
