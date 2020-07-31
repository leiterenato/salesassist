## Steps to Execute
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