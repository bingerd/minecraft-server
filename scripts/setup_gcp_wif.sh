set -euxo pipefail

PROJECT_ID="minecraft-481513"
REPO="bingerd/minecraft-server"

# Get project number
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")

# Create workload identity pool if it doesn't exist
if ! gcloud iam workload-identity-pools describe github-pool --location=global --project=$PROJECT_ID >/dev/null 2>&1; then
  gcloud iam workload-identity-pools create "github-pool" \
    --project=$PROJECT_ID \
    --location="global" \
    --display-name="GitHub Actions Pool"
fi

# Create workload identity provider if it doesn't exist
if ! gcloud iam workload-identity-pools providers describe github-provider --location=global --workload-identity-pool=github-pool --project=$PROJECT_ID >/dev/null 2>&1; then
  gcloud iam workload-identity-pools providers create-oidc "github-provider" \
    --project=$PROJECT_ID \
    --location="global" \
    --workload-identity-pool="github-pool" \
    --display-name="GitHub Actions Provider" \
    --attribute-mapping="google.subject=assertion.sub,attribute.repository=assertion.repository" \
    --attribute-condition="assertion.repository=='$REPO'" \
    --issuer-uri="https://token.actions.githubusercontent.com"
fi

# Create service account if it doesn't exist
if ! gcloud iam service-accounts describe github-actions-sa@$PROJECT_ID.iam.gserviceaccount.com --project=$PROJECT_ID >/dev/null 2>&1; then
  gcloud iam service-accounts create "github-actions-sa" \
    --project=$PROJECT_ID \
    --display-name="GitHub Actions Service Account"
fi

# Grant necessary permissions
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:github-actions-sa@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/editor"

# Allow the GitHub repo to impersonate the service account
gcloud iam service-accounts add-iam-policy-binding \
  "github-actions-sa@$PROJECT_ID.iam.gserviceaccount.com" \
  --project=$PROJECT_ID \
  --role="roles/iam.workloadIdentityUser" \
  --member="principalSet://iam.googleapis.com/projects/$PROJECT_NUMBER/locations/global/workloadIdentityPools/github-pool/attribute.repository/$REPO"

# Output the values you need for GitHub secrets
echo "Add these to your GitHub repository secrets:"
echo "WIF_PROVIDER: projects/$PROJECT_NUMBER/locations/global/workloadIdentityPools/github-pool/providers/github-provider"
echo "WIF_SERVICE_ACCOUNT: github-actions-sa@$PROJECT_ID.iam.gserviceaccount.com"