# Deploy to Google Cloud

### Step 1: Build Image with Cloud Build
gcloud builds submit --tag gcr.io/cool-ml-demos/salesassist-restore

### Step 2: Deploy to Cloud Run using YAML file
gcloud beta run services replace service.yaml --platform managed

### Step 3: Allow external access
gcloud run services add-iam-policy-binding restore \
    --member="allUsers" \
    --role="roles/run.invoker"

#### Execute locally
export PROJECTID="cool-ml-demos"
go run receiverapi.go

PORT=8080 && docker run \
-p 9090:${PORT} \
-e PORT=${PORT} \
-e K_SERVICE=dev \
-e PROJECTIDDATA=cool-ml-demos \
-e K_CONFIGURATION=dev \
-e K_REVISION=dev-00001 \
-e GOOGLE_APPLICATION_CREDENTIALS=/Users/renatoleite/Documents/google-cloud-sdk/cool-ml-demos-80c3372293d6.json \
-v $GOOGLE_APPLICATION_CREDENTIALS:/Users/renatoleite/Documents/google-cloud-sdk/cool-ml-demos-80c3372293d6.json:ro \
gcr.io/cool-ml-demos/salesassist-restore