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


### BigQuery Schema

[
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
        "mode": "NULLABLE"
    }
]