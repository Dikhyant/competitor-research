# Deploying to Render

This guide will help you deploy your Django competitor research app to Render.

## Prerequisites

1. A GitHub account with your code pushed to a repository
2. A Render account (sign up at https://render.com)
3. Your environment variables ready (OpenAI API key, Supabase credentials, etc.)

## Step-by-Step Deployment

### 1. Push Your Code to GitHub

Make sure all your code is committed and pushed to a GitHub repository:

```bash
git add .
git commit -m "Prepare for Render deployment"
git push origin main
```

### 2. Create a Render Account

1. Go to https://render.com
2. Sign up or log in
3. Connect your GitHub account

### 3. Create a New Web Service

1. In the Render dashboard, click "New +" and select "Web Service"
2. Connect your GitHub repository
3. Render will automatically detect the `render.yaml` file

### 4. Configure Environment Variables

In the Render dashboard, go to your service's "Environment" tab and add the following environment variables:

**Required:**
- `SECRET_KEY` - Django secret key (Render can auto-generate this, or you can set your own)
- `DEBUG` - Set to `False` for production
- `ALLOWED_HOSTS` - Your Render service URL (e.g., `your-app-name.onrender.com`)
- `DATABASE_URL` - Your PostgreSQL database connection string (if using Render's PostgreSQL)

**API Keys:**
- `OPENAI_API_KEY` - Your OpenAI API key
- `SUPABASE_URL` - Your Supabase project URL
- `SUPABASE_KEY` - Your Supabase API key

### 5. Set Up Database (Optional)

If you need a PostgreSQL database:

1. In Render dashboard, click "New +" and select "PostgreSQL"
2. Create a new database
3. Copy the "Internal Database URL" 
4. Add it as `DATABASE_URL` environment variable in your web service

### 6. Deploy

1. Render will automatically start building and deploying your app
2. The build process will:
   - Install dependencies from `requirements.txt`
   - Run `collectstatic` to gather static files
   - Start the app with Gunicorn

### 7. Run Migrations

After the first deployment, you need to run database migrations:

1. In Render dashboard, go to your service
2. Click on "Shell" tab
3. Run: `python manage.py migrate`
4. (Optional) Create a superuser: `python manage.py createsuperuser`

## Configuration Files

### render.yaml
This file configures your Render service automatically. It includes:
- Build command
- Start command (Gunicorn)
- Environment variables
- Python version

### settings.py Updates
The settings have been updated to:
- Use WhiteNoise for static file serving
- Handle Render's hostnames in ALLOWED_HOSTS
- Support environment-based configuration

## Troubleshooting

### Static Files Not Loading
- Make sure `collectstatic` runs during build (it's in the buildCommand)
- Check that WhiteNoise middleware is enabled in settings.py

### Database Connection Issues
- Verify your `DATABASE_URL` is correctly formatted
- For Render PostgreSQL, use the "Internal Database URL" for better performance
- Check that your database allows connections from Render's IPs

### Environment Variables
- Make sure all required environment variables are set in Render dashboard
- Check that variable names match exactly (case-sensitive)

### Build Failures
- Check the build logs in Render dashboard
- Ensure all dependencies are in `requirements.txt`
- Verify Python version compatibility

## Post-Deployment

1. **Set up a custom domain** (optional):
   - Go to your service settings
   - Add your custom domain
   - Update `ALLOWED_HOSTS` to include your domain

2. **Enable auto-deploy**:
   - Render automatically deploys on git push (enabled by default)
   - You can disable this in service settings

3. **Monitor your app**:
   - Check logs in the Render dashboard
   - Set up alerts for errors

## Notes

- The free tier on Render spins down after 15 minutes of inactivity
- Your first request after spin-down may take 30-60 seconds
- Consider upgrading to a paid plan for always-on service
- Static files are served via WhiteNoise (no need for separate static file service)

