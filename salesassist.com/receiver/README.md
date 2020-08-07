# Deploy to Google Cloud

### Step 1: Build Image with Cloud Build
gcloud builds submit --tag gcr.io/cool-ml-demos/salesassist-receiver

### Step 2: Deploy to Cloud Run using YAML file
gcloud beta run services replace service.yaml

### Step 3: Allow external access
gcloud run services add-iam-policy-binding salesassist \
    --member="allUsers" \
    --role="roles/run.invoker"

#### Execute locally
export PROJECTID="cool-ml-demos"
export TOPICID="sales-assist"
go run main.go