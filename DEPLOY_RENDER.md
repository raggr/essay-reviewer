# Deploying Essay Reviewer to Render

**Time required:** ~20 minutes  
**Cost:** Free tier available (spins down after inactivity); $7/mo for always-on

---

## What you need before starting

- A [GitHub](https://github.com) account
- A [Render](https://render.com) account (free to sign up)
- A [Supabase](https://supabase.com) account (free to sign up) — for storing essays and reviews
- This project folder

---

## Step 1 — Set up Supabase

Supabase is where opted-in essays and reviews are stored.

1. Go to [supabase.com](https://supabase.com) and create a free account
2. Click **New Project**, give it a name (e.g. `essay-reviewer`), choose a region, set a database password and save it somewhere safe
3. Once the project is ready, click **SQL Editor** in the left sidebar
4. Open the file `supabase_setup.sql` from this project, paste its contents into the editor, and click **Run**. This creates the `reviews` table.
5. Go to **Project Settings** → **API**. You need two values:
   - **Project URL** — looks like `https://xxxx.supabase.co`
   - **Service role key** — under "Project API keys" (use the `service_role` key, not `anon`)

Keep these handy — you'll paste them into Render in Step 3.

---

## Step 2 — Push the project to GitHub

Open Terminal and run the following. Replace `YOUR_GITHUB_USERNAME` with your actual GitHub username.

```bash
cd path/to/essay-reviewer-public

git init
git add .
git commit -m "Initial deploy"
```

Go to [github.com/new](https://github.com/new) and create a **new empty repository** called `essay-reviewer`. Do **not** tick "Add a README file".

Then run:

```bash
git remote add origin https://github.com/YOUR_GITHUB_USERNAME/essay-reviewer.git
git branch -M main
git push -u origin main
```

---

## Step 3 — Create a Web Service on Render

1. Go to [dashboard.render.com](https://dashboard.render.com) and click **New +** → **Web Service**
2. Click **Connect a repository** and select your `essay-reviewer` repo
3. Confirm the settings:

| Field | Value |
|---|---|
| **Name** | `essay-reviewer` |
| **Region** | Closest to your users |
| **Branch** | `main` |
| **Runtime** | `Python 3` |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `python server.py` |

4. Scroll down to **Environment Variables** and add these two:

| Key | Value |
|---|---|
| `SUPABASE_URL` | Your Supabase project URL |
| `SUPABASE_KEY` | Your Supabase service role key |

5. Under **Instance Type**, select **Free** (or Starter at $7/mo for always-on)
6. Click **Create Web Service**

Render will build and deploy — takes 2–4 minutes the first time.

---

## Step 4 — Verify storage is working

1. Visit your Render URL and run a test review with the consent box ticked
2. Go to Supabase → **Table Editor** → `reviews` — you should see a new row appear

If no row appears, check the Render **Logs** tab for any `[storage]` error lines.

---

## Step 5 — (Optional) Add a custom domain

In your Render service dashboard, go to **Settings** → **Custom Domains** and follow the instructions.

---

## Viewing and exporting your data

In Supabase, go to **Table Editor** → `reviews` to browse all stored essays and reviews. To export to CSV: click the download icon at the top right of the table view.

---

## Important notes

**Free tier cold starts:** Render's free tier spins down after ~15 minutes of inactivity. The first request after quiet will take 30–60 seconds. Upgrade to Starter ($7/mo) to avoid this.

**No API key on the server:** Users bring their own Anthropic API key. You do not need to set `ANTHROPIC_API_KEY` as an environment variable.

**Supabase free tier limits:** 500 MB database storage, 5 GB bandwidth per month. Sufficient for many thousands of reviews.

**Updating the app:** Any `git push` to `main` triggers an automatic Render redeploy.

---

## Troubleshooting

**Build fails:** Check `requirements.txt` contains `anthropic`, `click`, and `supabase`.

**Storage not working:** Confirm `SUPABASE_URL` and `SUPABASE_KEY` are set correctly in Render's environment variables. Check Render logs for `[storage]` lines.

**Reviews fail with auth error:** The user's API key is invalid or has no credit.

**Port errors:** Render sets the `PORT` environment variable automatically — the server reads it, no action needed.


**Time required:** ~15 minutes  
**Cost:** Free tier available (spins down after inactivity); $7/mo for always-on

---

## What you need before starting

- A [GitHub](https://github.com) account
- A [Render](https://render.com) account (free to sign up)
- This project folder

---

## Step 1 — Push the project to GitHub

Open Terminal and run the following commands. Replace `YOUR_GITHUB_USERNAME` with your actual GitHub username.

```bash
cd path/to/essay-reviewer-public

git init
git add .
git commit -m "Initial deploy"
```

Now go to [github.com/new](https://github.com/new) and create a **new empty repository** called `essay-reviewer`. Do **not** tick "Add a README file".

Then run:

```bash
git remote add origin https://github.com/YOUR_GITHUB_USERNAME/essay-reviewer.git
git branch -M main
git push -u origin main
```

Your code is now on GitHub.

---

## Step 2 — Create a Web Service on Render

1. Go to [dashboard.render.com](https://dashboard.render.com) and click **New +** → **Web Service**
2. Click **Connect a repository** and select your `essay-reviewer` repo
3. Render will auto-detect the settings. Confirm they match:

| Field | Value |
|---|---|
| **Name** | `essay-reviewer` (or whatever you like) |
| **Region** | Choose the one closest to your users |
| **Branch** | `main` |
| **Runtime** | `Python 3` |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `python server.py` |

4. Under **Instance Type**, select **Free** (or Starter at $7/mo if you want it always on)
5. Click **Create Web Service**

Render will now build and deploy the app. This takes 2–4 minutes the first time.

---

## Step 3 — Check it's working

Once the build log shows `==> Your service is live`, click the URL at the top of the page (it looks like `https://essay-reviewer-xxxx.onrender.com`).

You should see the Essay Reviewer interface. Enter an Anthropic API key and run a test review.

---

## Step 4 — (Optional) Add a custom domain

1. In your Render service dashboard, go to **Settings** → **Custom Domains**
2. Click **Add Custom Domain** and follow the instructions to point your domain's DNS at Render

---

## Important notes

**Free tier behaviour:** Render's free tier spins the service down after ~15 minutes of inactivity. The first request after a period of quiet will take 30–60 seconds to wake up. If you want the service always responsive, upgrade to the Starter plan ($7/mo).

**No API key needed on the server:** The app is designed so each user provides their own Anthropic API key. You do not need to set any environment variables in Render.

**Updating the app:** Any `git push` to your `main` branch will automatically trigger a new Render deployment.

**Logs:** In the Render dashboard, click **Logs** to see live server output and debug any errors.

---

## Troubleshooting

**Build fails with "module not found":** Check that `requirements.txt` lists `anthropic` and `click`.

**App loads but reviews fail:** The user's API key may be invalid or have no credit. The error message in the UI will indicate which.

**Port errors:** The server reads the `PORT` environment variable automatically — Render sets this for you, so no configuration needed.
