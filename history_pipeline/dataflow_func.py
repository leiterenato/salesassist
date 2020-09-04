def start_batch_dataflow(event, context):
    """Background Cloud Function to be triggered by Pub/Sub.
    Args:
         event (dict):  The dictionary with data specific to this type of
         event. The `data` field contains the PubsubMessage message. The
         `attributes` field will contain custom attributes if there are any.
         context (google.cloud.functions.Context): The Cloud Functions event
         metadata. The `event_id` field contains the Pub/Sub message ID. The
         `timestamp` field contains the publish time.
    """

    from googleapiclient.discovery import build
    from datetime import datetime

    project = 'cool-ml-demos'
    location = 'us-east1'
    template='gs://salesassist-history/templates/batch-template'
    job = ('batch-' + 
            str(datetime.now().date()) + '-' +
            str(datetime.now().time().hour) + '-' +
            str(datetime.now().time().minute))

    dataflow = build('dataflow', 'v1b3')

    request = dataflow.projects().templates().launch(
        projectId=project,
        gcsPath=template,
        body={
            'jobName': job
        }
    )

    response = request.execute()
