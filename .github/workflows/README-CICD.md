# CI/CD Pipeline Documentation

## Overview

This repository uses GitHub Actions for automated deployment to Google Cloud Run with Cloud SQL.

### Workflow Sequence

```
Developer pushes to `dev` branch
         ↓
Auto-Sync Dev to Test (auto-sync-dev-to-test.yml)
         ↓
Changes merged to `test` branch
         ↓
Deploy Test to Cloud Run (deploy-test-cloudrun.yml)
         ↓
Build Docker Image → Push to Artifact Registry → Deploy to Cloud Run
         ↓
Health Check & Notifications
```

## 🔑 Required GitHub Secrets

To set up the CI/CD pipeline, add these secrets to your GitHub repository:

### Navigate to: `Settings` → `Secrets and variables` → `Actions` → `New repository secret`

| Secret Name | Description | How to Get It |
|-------------|-------------|---------------|
| `GCP_SA_KEY` | Google Cloud Service Account Key (JSON) | See [GCP Service Account Setup](#gcp-service-account-setup) |
| `CLOUD_SQL_DB_PASSWORD` | Cloud SQL `weedgo` user password | From `/tmp/cloudsql-weedgo-password.txt` |

### GCP Service Account Setup

1. **Create Service Account:**
   ```bash
   gcloud iam service-accounts create github-actions-deployer \
     --display-name="GitHub Actions Deployer"
   ```

2. **Grant Required Permissions:**
   ```bash
   # Cloud Run Admin
   gcloud projects add-iam-policy-binding weedgo-uat-2025 \
     --member="serviceAccount:github-actions-deployer@weedgo-uat-2025.iam.gserviceaccount.com" \
     --role="roles/run.admin"

   # Artifact Registry Writer
   gcloud projects add-iam-policy-binding weedgo-uat-2025 \
     --member="serviceAccount:github-actions-deployer@weedgo-uat-2025.iam.gserviceaccount.com" \
     --role="roles/artifactregistry.writer"

   # Cloud SQL Client (for migrations)
   gcloud projects add-iam-policy-binding weedgo-uat-2025 \
     --member="serviceAccount:github-actions-deployer@weedgo-uat-2025.iam.gserviceaccount.com" \
     --role="roles/cloudsql.client"

   # Service Account User (for Cloud Run)
   gcloud projects add-iam-policy-binding weedgo-uat-2025 \
     --member="serviceAccount:github-actions-deployer@weedgo-uat-2025.iam.gserviceaccount.com" \
     --role="roles/iam.serviceAccountUser"
   ```

3. **Create and Download Key:**
   ```bash
   gcloud iam service-accounts keys create ~/github-actions-key.json \
     --iam-account=github-actions-deployer@weedgo-uat-2025.iam.gserviceaccount.com
   ```

4. **Add to GitHub Secrets:**
   - Copy the entire contents of `~/github-actions-key.json`
   - Go to GitHub: `Settings` → `Secrets` → `New secret`
   - Name: `GCP_SA_KEY`
   - Value: Paste the JSON content
   - Click "Add secret"

5. **Clean up local key:**
   ```bash
   rm ~/github-actions-key.json
   ```

## 🚀 How to Use

### Automatic Deployment

1. **Make changes** in your local environment
2. **Commit and push** to the `dev` branch:
   ```bash
   git checkout dev
   git add .
   git commit -m "feat: your changes"
   git push origin dev
   ```
3. **Automatic process:**
   - `auto-sync-dev-to-test.yml` merges `dev` → `test`
   - `deploy-test-cloudrun.yml` builds and deploys to Cloud Run
   - Health checks verify deployment success

### Manual Deployment

Trigger a manual deployment from GitHub Actions:

1. Go to `Actions` tab
2. Select "Deploy Test to Cloud Run"
3. Click "Run workflow"
4. Select `test` branch
5. Optionally enable "Run database migrations"
6. Click "Run workflow"

### Manual Deployment with Migrations

To run database migrations during deployment:

1. Go to `Actions` → "Deploy Test to Cloud Run"
2. Click "Run workflow"
3. Check ✅ "Run database migrations"
4. Click "Run workflow"

## 📊 Monitoring Deployments

### View Logs

**GitHub Actions:**
- Repository → `Actions` tab → Select workflow run

**Cloud Run Logs:**
```bash
gcloud run services logs read weedgo-test --region=us-central1
```

**Cloud SQL Logs:**
```bash
gcloud sql operations list --instance=weedgo-test-db
```

### Health Check

After deployment completes, verify health:

```bash
curl https://weedgo-test-1078824501673.us-central1.run.app/health
```

Expected response:
```json
{
  "status": "healthy",
  "version": "5.0.0",
  "features": {
    "streaming": true,
    "function_schemas": true
  }
}
```

## 🔧 Troubleshooting

### Build Fails

**Issue:** Docker build fails
**Solution:**
1. Check Dockerfile syntax in `src/Backend/Dockerfile`
2. Verify all dependencies are in `requirements.txt`
3. Check GitHub Actions logs for specific error

### Deployment Fails

**Issue:** Cloud Run deployment fails
**Solution:**
1. Verify service account has correct permissions
2. Check if Cloud SQL instance is running
3. Verify environment variables are correct

### Health Check Fails

**Issue:** Service deploys but health check fails
**Solution:**
1. Check Cloud Run logs:
   ```bash
   gcloud run services logs read weedgo-test --region=us-central1 --limit=50
   ```
2. Verify database connection settings
3. Check if Cloud SQL instance is accessible

### Migrations Fail

**Issue:** Database migrations don't complete
**Solution:**
1. Check if Cloud SQL Proxy can connect
2. Verify database password is correct in GitHub Secrets
3. Run migrations manually:
   ```bash
   # See manual migration steps in main README
   ```

## 🔄 Workflow Files

| File | Purpose | Trigger |
|------|---------|---------|
| `auto-sync-dev-to-test.yml` | Auto-merge dev → test | Push to `dev` |
| `deploy-test-cloudrun.yml` | Deploy to Cloud Run | Push to `test` |
| `deploy-multi-env.yml` | Multi-environment deployment | Push to `main`/`staging`/`release` |

## 📝 Environment Variables

The following environment variables are automatically set during Cloud Run deployment:

| Variable | Value | Purpose |
|----------|-------|---------|
| `ENVIRONMENT` | test | Environment identifier |
| `DB_HOST` | /cloudsql/weedgo-uat-2025:us-central1:weedgo-test-db | Cloud SQL Unix socket |
| `DB_PORT` | 5432 | PostgreSQL port |
| `DB_NAME` | ai_engine | Database name |
| `DB_USER` | weedgo | Database user |
| `DB_PASSWORD` | (from secret) | Database password |

## 🛡️ Security Notes

- ✅ Service account uses principle of least privilege
- ✅ Secrets are stored in GitHub Secrets (encrypted)
- ✅ Database password is never exposed in logs
- ✅ Cloud SQL uses private IP + Unix sockets (no public IP needed)
- ⚠️  Never commit service account keys to the repository

## 🎯 Next Steps

1. ✅ Set up GitHub Secrets (see above)
2. ✅ Test the pipeline by pushing to `dev`
3. ✅ Monitor the deployment in GitHub Actions
4. ✅ Verify health check passes
5. 🔜 Set up Slack/Discord notifications (optional)
6. 🔜 Add integration tests to the pipeline (optional)

## 📚 Additional Resources

- [Google Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Google Cloud SQL Documentation](https://cloud.google.com/sql/docs)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
