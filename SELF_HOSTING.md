# Self-Hosting Backend on Mac Mini

This is excellent! Hosting on your Mac Mini solves the YouTube "Sign in" error because YouTube trusts your home internet connection (Residential IP) much more than cloud servers like Render.

## The Challenge
Your Mac Mini is behind your home router (`localhost:8000`). Netlify (on the public internet) cannot see it directly.

## The Solution: Cloudflare Tunnel (Free & Secure)
We will use Cloudflare Tunnel to create a public URL (e.g., `https://my-mac-server.trycloudflare.com`) that points to your local server.

### Step 1: Start your Backend
Make sure your backend is running on the Mac Mini:
```bash
cd ~/Desktop/downloader
source venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```
*(Keep this terminal open)*

### Step 2: Install Cloudflare Tunnel
Open a **new terminal tab** and run:

```bash
brew install cloudflared
```

### Step 3: Start the Tunnel
Run this command to create a temporary public URL:

```bash
cloudflared tunnel --url http://localhost:8000
```

You will see output like this:
```text
+--------------------------------------------------------------------------------------------+
|  Your quick Tunnel has been created! Visit it at (it may take some time to be reachable):  |
|  https://random-name-123.trycloudflare.com                                               |
+--------------------------------------------------------------------------------------------+
```
**Copy that URL.** This is your public backend URL.

### Step 4: Update Frontend (index.html)
1.  Open `/Users/muhammadsallahuddinhamzah/Desktop/downloader/frontend/index.html`.
2.  Find line ~476: `const API_BASE = ...`.
3.  Replace it with your new Cloudflare URL:
    ```javascript
    const API_BASE = "https://random-name-123.trycloudflare.com";
    ```

### Step 5: Redeploy Frontend
1.  Drag the `frontend` folder to Netlify again.
2.  Now your Netlify site talks to your Mac Mini!

---

## Alternative: Ngrok (Easier but temporary)
If you prefer Ngrok:
1.  `brew install ngrok/ngrok/ngrok`
2.  `ngrok http 8000`
3.  Copy the `https://....ngrok-free.app` URL.
4.  Update `index.html` and deploy.

### Important Notes
- **Keep the Mac Mini On**: The server must be running for the site to work.
- **Dynamic URLs**: The `trycloudflare` or `ngrok` URLs change every time you restart standard tunnels.
- **Permanent URL**: To get a permanent URL (like `api.mysite.com`), you need a free Cloudflare account and to run: `cloudflared tunnel login`.

---

## Option 3: Tailscale (If you already use it)

If you have Tailscale installed, you can use **Tailscale Funnel** to make it public.

**Note**: Standard Tailscale IPs (`100.x.y.z`) **will NOT work** with Netlify because Netlify isn't on your private VPN. You must use "Funnel".

1.  **Enable Funnel**:
    Go to [Tailscale Admin Console](https://login.tailscale.com/admin/acls/file) and add this to your ACLs:
    ```json
    "nodeAttrs": [
      {
        "target": ["autogroup:member"],
        "attr": ["funnel"]
      }
    ]
    ```

2.  **Start Funnel**:
    ```bash
    tailscale funnel 8000
    ```

3.  **Get URL**:
    It will give you a URL like `https://my-mac-mini.tailnet-name.ts.net`.
    Use this URL in your `index.html`.
