from __future__ import absolute_import

import argparse
import logging
import json
import time

from past.builtins import unicode

import apache_beam as beam
from apache_beam.io import fileio
from apache_beam.options.pipeline_options import PipelineOptions
from apache_beam.options.pipeline_options import SetupOptions
from apache_beam.options.pipeline_options import StandardOptions
from apache_beam.options.pipeline_options import GoogleCloudOptions


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

    # We use the save_main_session option because one or more DoFn's in this
    # workflow rely on global context (e.g., a module imported at module level).
    pipeline_options = PipelineOptions(pipeline_args)
    pipeline_options.view_as(SetupOptions).save_main_session = save_main_session
    pipeline_options.view_as(StandardOptions).streaming = True

    with beam.Pipeline(options=pipeline_options) as p:
        # Read from PubSub into a PCollection.
        messages = (
            p
             | 'Read from PubSub' >> 
                    beam.io.ReadFromPubSub(subscription=known_args.input_subscription)
                        .with_output_types(bytes)
             | 'JSONParse' >> beam.Map(json.loads)
             | 'Write to BigQuery' >> beam.io.WriteToBigQuery(
                    known_args.output_bigquery,
                    write_disposition=beam.io.BigQueryDisposition.WRITE_APPEND))


if __name__ == '__main__':
    logging.getLogger().setLevel(logging.INFO)
    run()