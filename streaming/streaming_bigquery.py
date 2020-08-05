import argparse
import logging
import json
import re

import apache_beam as beam


# [TODO] 
# - Use timepartitioning to write to BQ

def run_pipeline(known_args, pipeline_args):
    # Define and run pipeline
    with beam.Pipeline(argv=pipeline_args) as p:
        messages = (
            p
            | 'Read from PubSub' >> 
                beam.io.ReadFromPubSub(subscription=known_args.input_subscription)
                    .with_output_types(bytes)
            | 'ParseJson' >> beam.ParDo(ParseJson())
                    .with_outputs('json_decode_error', main='cleared_json'))

        json_error =  messages.json_decode_error
        json_cleared = messages.cleared_json

        json_error | 'Write Errors to BigQuery' >> beam.io.WriteToBigQuery(
                        known_args.output_error_bigquery,
                        schema=TablesProperties.error_schema,
                        create_disposition=beam.io.BigQueryDisposition.CREATE_IF_NEEDED,
                        write_disposition=beam.io.BigQueryDisposition.WRITE_APPEND)

        insert_errors = json_cleared | 'WritePayloadBigQuery' >> beam.io.WriteToBigQuery(
                            known_args.output_bigquery,
                            schema=TablesProperties.table_schema,
                            insert_retry_strategy='RETRY_ON_TRANSIENT_ERROR',
                            validate=False,
                            create_disposition=beam.io.BigQueryDisposition.CREATE_NEVER,
                            write_disposition=beam.io.BigQueryDisposition.WRITE_APPEND)

        insert_result = (
            insert_errors['FailedRows'] | 'WrapInsertionError' >> beam.ParDo(WrapInsertionError())
                | 'WriteInsertionErrorBigQuery' >> beam.io.WriteToBigQuery(
                            known_args.output_error_bigquery,
                            schema=TablesProperties.error_schema,
                            insert_retry_strategy='RETRY_ON_TRANSIENT_ERROR',
                            validate=False,
                            create_disposition=beam.io.BigQueryDisposition.CREATE_NEVER,
                            write_disposition=beam.io.BigQueryDisposition.WRITE_APPEND)
            )


class TablesProperties:
    table_schema = {
        'fields': [{
            'name': 'meetingid', 'type': 'STRING', 'mode': 'REQUIRED'
        }, {
            'name': 'timestamp_transcription', 'type': 'TIMESTAMP', 'mode': 'REQUIRED'
        }, {
            'name': 'transcription', 'type': 'STRING', 'mode': 'REQUIRED'
        }]
    }

    error_schema = {
        'fields': [{
            'name': 'meetingid', 'type': 'STRING', 'mode': 'NULLABLE'
        }, {
            'name': 'payload', 'type': 'STRING', 'mode': 'NULLABLE'
        }, {
            'name': 'error', 'type': 'STRING', 'mode': 'NULLABLE'
        }]
    }


class WrapInsertionError(beam.DoFn):
    def process(self, element):
        meeting = re.search('[a-z]+-[a-z]+-[a-z]+', str(element[1]))
        if meeting:
            meeting = meeting.group()
        else:
            meeting = ''
        error_message = {'meetingid':meeting, 'payload':str(element), 'error':'bigquery_insertion_error'}
        yield error_message


class ParseJson(beam.DoFn):
    def process(self, element):
        try:
            element = json.loads(element)
        except ValueError as e:
            meeting = re.search('[a-z]+-[a-z]+-[a-z]+', str(element))
            if meeting:
                meeting = meeting.group()
            else:
                meeting = ''
            error_message = {'meetingid':meeting, 'payload':str(element), 'error':e}
            yield beam.pvalue.TaggedOutput('json_decode_error', error_message)
        else:
            yield element


if __name__ == '__main__':
    logging.getLogger().setLevel(logging.INFO)

    parser = argparse.ArgumentParser(prog='Assist Streaming')
    parser.add_argument(
        '--input_subscription',
        dest='input_subscription',
        default='projects/cool-ml-demos/subscriptions/sales-assist-subscription',
        help='Input subscription')
    parser.add_argument(
        '--output_bigquery',
        dest='output_bigquery',
        default='cool-ml-demos:salesassist.history',
        help='Output table in BigQuery.')
    parser.add_argument(
        '--output_error_bigquery',
        dest='output_error_bigquery',
        default='cool-ml-demos:salesassist.history_error',
        help='Error output table in BigQuery.')
    known_args, pipeline_args = parser.parse_known_args(None)

    run_pipeline(known_args, pipeline_args)
