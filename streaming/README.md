## PubSub to BigQuery (streaming)
gcloud dataflow jobs run sa-pb-bigquery --gcs-location gs://dataflow-templates-us-east1/latest/PubSub_to_BigQuery --region us-east1 --worker-region us-east1 --staging-location gs://salesassist-history/tmp/ --parameters inputTopic=projects/cool-ml-demos/topics/sales-assist,outputTableSpec=cool-ml-demos:salesassist.history,outputDeadletterTable=cool-ml-demos:salesassist.history_deadletter

## PubSub to GCS (streaming)
gcloud dataflow jobs run sa-ps-gcs --gcs-location gs://dataflow-templates-us-east1/latest/Cloud_PubSub_to_GCS_Text --region us-east1 --worker-region us-east1 --staging-location gs://salesassist-history/tmp/ --parameters inputTopic=projects/cool-ml-demos/topics/sales-assist,outputDirectory=gs://salesassist-history/,outputFilenamePrefix=meetid,outputFilenameSuffix=.json

## Steps to Execute custom script
python streaming.py \
  --runner DataflowRunner \
  --project cool-ml-demos \
  --region us-east1 \
  --streaming \
  --temp_location gs://salesassist-history/tmp/ \
  --input_subscription "projects/cool-ml-demos/subscriptions/sales-assist-subscription" \
  --output_bigquery "cool-ml-demos:salesassist.history" \
  --output_bucket "gs://salesassist-history"

## Local
python streaming.py \
  --streaming \
  --temp_location gs://salesassist-history/tmp/ \
  --input_subscription "projects/cool-ml-demos/subscriptions/sales-assist-subscription" \
  --output_bigquery "cool-ml-demos:salesassist.history" \
  --output_bucket "gs://salesassist-history"


### Payload
{"meetingid":"ccc-ddd-eee", "phrase":"xxxxx"}