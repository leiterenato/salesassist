# Dataflow Streaming
### Bigquery (long-term history)
python streaming_bigquery.py \
  --runner DataflowRunner \
  --project cool-ml-demos \
  --region us-east1 \
  --streaming \
  --temp_location gs://salesassist-history/tmp/ \
  --input_subscription "projects/cool-ml-demos/subscriptions/sales-assist-subscription" \
  --output_bigquery "cool-ml-demos:salesassist.history" \
  --output_error_bigquery "cool-ml-demos:salesassist.history_error"

### Firebase (short-term history)
python streaming_firestore.py \
--streaming \
--requirements_file requirements.txt

### Local Streaming (PubSub to BigQuery)
python test_JSONParse_streaming_bigquery.py \
  --streaming \
  --temp_location gs://salesassist-history/tmp/

# Dataflow Batch (storage)
### Create dataflow template
python batch_storage.py \
    --runner DataflowRunner \
    --project cool-ml-demos \
    --staging_location gs://salesassist-history/staging \
    --temp_location gs://salesassist-history/tmp \
    --template_location gs://salesassist-history/templates/batch-template

### Create Cloud Scheduler
 - Point to Topic in PubSub: projects/cool-ml-demos/topics/sales-assist-batch-scheduler

### Create Cloud Function
 - Trigger by PubSub
 - Paste Func in inline editor

python batch_storage.py \
  --project cool-ml-demos \
  --runner DataflowRunner \
  --region us-east1 \
  --save_main_session True \
  --temp_location gs://salesassist-history/tmp/ 

### Local Batch (BigQuery to GCS)
python batch_storage.py \
  --project cool-ml-demos \
  --temp_location gs://salesassist-history/tmp/ 

### Payload (tests)
{"uid":"bbbbbbb", "meetingID":"xxx-xxxx-xxx", "speaker": "GOOGLER", "transcript": "machine learning", "start": "2020-09-04 13:45:00", "end": "2020-08-22 13:45:00"}

### BigQuery Schema
[
    {
        "name": "uid",
        "type": "STRING",
        "mode": "REQUIRED"
    },
    {
        "name": "meetingid",
        "type": "STRING",
        "mode": "REQUIRED"
    },
    {
        "name": "speaker",
        "type": "STRING",
        "mode": "REQUIRED"
    },
    {
        "name": "transcript",
        "type": "STRING",
        "mode": "REQUIRED"
    },
    {
        "name": "start",
        "type": "DATETIME",
        "mode": "REQUIRED"
    },
    {
        "name": "end",
        "type": "DATETIME",
        "mode": "REQUIRED"
    },
    {
        "name": "response",
        "type": "RECORD",
        "fields": [
            {
                "name": "title",
                "type": "STRING",
                "mode": "NULLABLE"
            },
            {
                "name": "content",
                "type": "STRING",
                "mode": "NULLABLE"
            }
        ],
        "mode": "REPEATED"
    }
]