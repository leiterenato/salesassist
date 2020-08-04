from __future__ import absolute_import

import argparse
import logging
import json
import time

from past.builtins import unicode

import apache_beam as beam
from apache_beam.io import fileio

# [TODO] Tratar erro de inserção no BigQuery

def run(argv=None, save_main_session=True):
    """Build and run the pipeline."""

    parser = argparse.ArgumentParser(prog='Assist Streaming')
    parser.add_argument(
        '--input_subscription',
        dest='input_subscription',
        default='projects/cool-ml-demos/subscriptions/sales-assist-subscription',
        help='Input Subscription')
    parser.add_argument(
        '--output_bigquery',
        dest='output_bigquery',
        default='cool-ml-demos:salesassist.history',
        help='Output Table in BigQuery.')
    known_args, pipeline_args = parser.parse_known_args(argv)

    table_schema = {
        'fields': [{
            'name': 'meetingid', 'type': 'STRING', 'mode': 'REQUIRED'
        }, {
            'name': 'timestamp_transcription', 'type': 'TIMESTAMP', 'mode': 'REQUIRED'
        }, {
            'name': 'transcription', 'type': 'STRING', 'mode': 'REQUIRED'
        }]
    }

    with beam.Pipeline(argv=pipeline_args) as p:
        # Read from PubSub into a PCollection.
        messages = (
            p
            | 'Read from PubSub' >>
            beam.io.ReadFromPubSub(subscription=known_args.input_subscription)
                                        .with_output_types(bytes)
            | 'JSONParse' >> beam.Map(json.loads)
            | 'Write to BigQuery' >> beam.io.WriteToBigQuery(
                known_args.output_bigquery,
                schema=table_schema,
                create_disposition=beam.io.BigQueryDisposition.CREATE_IF_NEEDED,
                write_disposition=beam.io.BigQueryDisposition.WRITE_APPEND))


if __name__ == '__main__':
    logging.getLogger().setLevel(logging.INFO)
    run()
