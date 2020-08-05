## Steps to Execute Dataflow
python streaming.py \
  --runner DataflowRunner \
  --project cool-ml-demos \
  --region us-east1 \
  --streaming \
  --temp_location gs://salesassist-history/tmp/ \
  --input_subscription "projects/cool-ml-demos/subscriptions/sales-assist-subscription" \
  --output_bigquery "cool-ml-demos:salesassist.history" \
  --output_bucket "gs://salesassist-history"

## Local Streaming (PubSub to BigQuery)
python test_JSONParse_streaming_bigquery.py \
  --streaming \
  --temp_location gs://salesassist-history/tmp/

## Local Batch (BigQuery to GCS)
python streaming_storage.py \
  --temp_location gs://salesassist-history/tmp/ 

### Payload (tests)
    # test = [
    #     b'{"meetingid":"aaa-bbb-ccc", "transcription":"oi", "timestamp_transcription":"2020-08-24 12:44:31.744957 UTC"}',
    #     b'{"meetingid":"aaa-bbb-ccc", "transcription":"oi", "timestamp_transcription":"2020-08-24 12:44:31.744957 UTC"}',
    #     b'{"meetingid":"aaa-bbb-ccc", "transcription":"oi"}',
    #     b'{meetingid":"aaa-bbb-ccc", "transcription":"oi", "timestamp_transcription":"2020-08-24 12:44:31.744957 UTC"}'
    # ]


gcloud pubsub topics publish sales-assist --message="{\"meetingid\":\"aaa-bbb-ccc\", \"transcription\":\"oi\", \"timestamp_transcription\":\"2020-08-24 12:44:31.744957 UTC\"}"
gcloud pubsub topics publish sales-assist --message="{\"meetingid\":\"aaa-bbb-ccc\", \"transcription\":\"oi\", \"timestamp_transcription\":\"2020-08-24 12:44:31.744957 UTC\"}"
gcloud pubsub topics publish sales-assist --message="{\"meetingid\":\"aaa-bbb-ccc\", \"transcription\":\"oi\", \"timestamp_transcription\":\"2020-08-21 12:44:31.744957 UTC\"}"
gcloud pubsub topics publish sales-assist --message="{\"meetingid\":\"aaa-bbb-ccc\", \"transcription\":\"oi\", \"timestamp_transcription\":\"2020-08-21 12:44:31.744957 UTC\"}"
gcloud pubsub topics publish sales-assist --message="{\"meetingid\":\"aaa-bbb-ccc\", \"transcription\":\"oi\", \"timestamp_transcription\":\"2020-08-21 12:44:31.744957 UTC\"}"
gcloud pubsub topics publish sales-assist --message="{\"meetingid\":\"aaa-bbb-ccc\", \"transcription\":\"oi\", \"timestamp_transcription\":\"2020-08-24 12:44:31.744957 UTC\"}"

gcloud pubsub topics publish sales-assist --message="{\"meetingid\":\"ddd-eee-fff\", \"transcription\":\"oi\", \"timestamp_transcription\":\"2020-08-24 12:44:31.744957 UTC\"}"
gcloud pubsub topics publish sales-assist --message="{\"meetingid\":\"ddd-eee-fff\", \"transcription\":\"oi\", \"timestamp_transcription\":\"2020-08-24 12:44:31.744957 UTC\"}"
gcloud pubsub topics publish sales-assist --message="{\"meetingid\":\"ddd-eee-fff\", \"transcription\":\"oi\", \"timestamp_transcription\":\"2020-08-24 12:44:31.744957 UTC\"}"
gcloud pubsub topics publish sales-assist --message="{\"meetingid\":\"ddd-eee-fff\", \"transcription\":\"oi\", \"timestamp_transcription\":\"2020-08-24 12:44:31.744957 UTC\"}"
gcloud pubsub topics publish sales-assist --message="{\"meetingid\":\"ddd-eee-fff\", \"transcription\":\"oi\", \"timestamp_transcription\":\"2020-08-24 12:44:31.744957 UTC\"}"
gcloud pubsub topics publish sales-assist --message="{\"meetingid\":\"ddd-eee-fff\", \"transcription\":\"oi\", \"timestamp_transcription\":\"2020-08-20 12:44:31.744957 UTC\"}"

gcloud pubsub topics publish sales-assist --message="{\"meetingid\":\"ddd-eee-fff\", \"transcription\":\"oi\", \"timestamp_transcription\":\"2020-08-02 12:44:31.744957 UTC\"}"
gcloud pubsub topics publish sales-assist --message="{\"meetingid\":\"ddd-eee-fff\", \"transcription\":\"oi\", \"timestamp_transcription\":\"2020-08-02 12:44:31.744957 UTC\"}"
