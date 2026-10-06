# Cloudflare Pages Password Protection Setup

## Overview
Password-protect your Theophysics analytics dashboard on Cloudflare Pages using Cloudflare Access.

---

## Method 1: Cloudflare Access (Recommended)

**Free for up to 50 users**

### Step 1: Enable Cloudflare Access

1. Go to your Cloudflare dashboard
2. Select your domain (faiththruphysics.com or theophysics.pages.dev)
3. Click **Zero Trust** in the left sidebar
4. Click **Access** → **Applications**
5. Click **Add an application**

### Step 2: Configure Application

1. **Select application type:** Self-hosted
2. **Application name:** Theophysics Analytics
3. **Session duration:** 24 hours (or your preference)
4. **Application domain:** 
   - If using Pages: `theophysics.pages.dev`
   - If using custom domain: `faiththruphysics.com`
5. **Path:** Leave blank to protect entire site, or use `/_paper_analytics` to protect only analytics
6. Click **Next**

### Step 3: Add Authentication Method

Choose one:

**Option A: One-Time PIN (Simplest)**
- Select **One-time PIN**
- Enter email addresses allowed to access
- Users get a code sent to their email each time

**Option B: Simple Password (PIN)**
- Select **Service Auth**
- Create a shared password
- Anyone with the password can access

**Option C: Google/Microsoft Login**
- Select **Login with Google** or **Login with Microsoft**
- Users authenticate with their accounts

### Step 4: Create Policy

1. **Policy name:** Allow Theophysics Access
2. **Action:** Allow
3. **Configure rules:**
   - For One-Time PIN: Add email addresses
   - For Service Auth: Create password
   - For OAuth: Select allowed domains
4. Click **Next** → **Add application**

---

## Method 2: Basic Auth (Simple Password)

**For quick password protection without Cloudflare Access**

### Create _headers file

Create a file named `_headers` in your deployment folder:

```
/*
  Basic-Auth: theophysics:YOUR_PASSWORD_HERE
```

Replace `YOUR_PASSWORD_HERE` with your desired password.

### Upload to Cloudflare Pages

1. Add `_headers` file to your `_paper_analytics` folder
2. Deploy to Cloudflare Pages
3. Users will see a browser login prompt
4. Username: `theophysics`
5. Password: Whatever you set

**Note:** This is less secure than Cloudflare Access but simpler.

---

## Method 3: Cloudflare Workers (Advanced)

**For custom password page**

Create a Cloudflare Worker with password protection:

```javascript
const PASSWORD = 'your-secure-password-here';

addEventListener('fetch', event => {
  event.respondWith(handleRequest(event.request));
});

async function handleRequest(request) {
  const url = new URL(request.url);
  
  // Check for password cookie
  const cookie = request.headers.get('Cookie');
  if (cookie && cookie.includes('auth=authenticated')) {
    return fetch(request);
  }
  
  // Check for password in query or form
  if (url.searchParams.get('password') === PASSWORD) {
    return new Response('', {
      status: 302,
      headers: {
        'Location': url.pathname,
        'Set-Cookie': 'auth=authenticated; Path=/; HttpOnly; Secure; Max-Age=86400'
      }
    });
  }
  
  // Show password form
  return new Response(`
    <!DOCTYPE html>
    <html>
    <head>
      <title>Theophysics - Password Required</title>
      <style>
        body {
          font-family: Arial, sans-serif;
          display: flex;
          justify-content: center;
          align-items: center;
          height: 100vh;
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }
        .login-box {
          background: white;
          padding: 40px;
          border-radius: 10px;
          box-shadow: 0 10px 30px rgba(0,0,0,0.3);
          text-align: center;
        }
        h1 { color: #667eea; }
        input {
          padding: 10px;
          font-size: 16px;
          border: 2px solid #667eea;
          border-radius: 5px;
          margin: 10px 0;
          width: 250px;
        }
        button {
          padding: 10px 30px;
          font-size: 16px;
          background: #667eea;
          color: white;
          border: none;
          border-radius: 5px;
          cursor: pointer;
        }
        button:hover { background: #764ba2; }
      </style>
    </head>
    <body>
      <div class="login-box">
        <h1>🔒 Theophysics Analytics</h1>
        <p>Password Required</p>
        <form method="GET">
          <input type="password" name="password" placeholder="Enter password" required>
          <br>
          <button type="submit">Access Dashboard</button>
        </form>
      </div>
    </body>
    </html>
  `, {
    headers: { 'Content-Type': 'text/html' }
  });
}
```

Deploy this Worker and route it to your Pages domain.

---

## Recommended Setup for You

**Use Method 1 (Cloudflare Access) with One-Time PIN:**

1. Free for up to 50 users
2. No password to remember
3. Email-based authentication
4. Can add/remove users easily
5. Works with RSS feed (Substack can still access)

**Configuration:**
- Application: `theophysics.pages.dev` or `faiththruphysics.com`
- Path: `/_paper_analytics` (protects analytics, leaves RSS feed public)
- Auth method: One-Time PIN
- Allowed emails: Your email + any collaborators

This way:
- ✅ Analytics dashboard is password-protected
- ✅ RSS feed at `/feed.xml` remains public for Substack
- ✅ Easy to share access with others
- ✅ No passwords to manage

---

## RSS Feed Considerations

**Important:** If you password-protect the entire site, Substack won't be able to access your RSS feed.

**Solution:**
- Protect only `/_paper_analytics/*` path
- Leave `/feed.xml` public
- Or use Cloudflare Access with a public policy for `/feed.xml`

**Cloudflare Access Rule for Public RSS:**
1. Create second policy for `/feed.xml`
2. Action: Bypass
3. This allows RSS feed to be public while protecting dashboards

---

## Next Steps

1. Choose your method (I recommend Cloudflare Access)
2. Set up password protection
3. Test access to dashboard
4. Verify RSS feed is still accessible
5. Deploy to Cloudflare Pages
