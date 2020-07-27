from __future__ import absolute_import

import argparse
import logging
import json

from past.builtins import unicode

import apache_beam as beam
import apache_beam.transforms.window as window
from apache_beam.options.pipeline_options import PipelineOptions
from apache_beam.options.pipeline_options import SetupOptions
from apache_beam.options.pipeline_options import StandardOptions

def run(save_main_session=True):
    """Build and run the pipeline."""

    input_subscription = 'projects/cool-ml-demos/subscriptions/sales-assist-subscription'

    # We use the save_main_session option because one or more DoFn's in this
    # workflow rely on global context (e.g., a module imported at module level).
    pipeline_options = PipelineOptions()
    pipeline_options.view_as(SetupOptions).save_main_session = save_main_session
    pipeline_options.view_as(StandardOptions).streaming = True

    with beam.Pipeline(options=pipeline_options) as p:
        # Read from PubSub into a PCollection.
        messages = (
            p
            | 'Read from PubSub' >> beam.io.ReadFromPubSub(subscription=input_subscription).
            with_output_types(bytes))

        lines = messages | 'JSONParse' >> beam.Map(lambda x: json.loads(x))
        

        counts = (
            lines
            | 'split' >>
            (beam.ParDo(WordExtractingDoFn()).with_output_types(unicode))
            | 'pair_with_one' >> beam.Map(lambda x: (x, 1))
            | beam.WindowInto(window.FixedWindows(15, 0))
            | 'group' >> beam.GroupByKey()
            | 'count' >> beam.Map(count_ones))

    # Format the counts into a PCollection of strings.
    def format_result(word_count):
      (word, count) = word_count
      return '%s: %d' % (word, count)

    output = (
        counts
        | 'format' >> beam.Map(format_result)
        | 'encode' >>
        beam.Map(lambda x: x.encode('utf-8')).with_output_types(bytes))

    # Write to PubSub.
    # pylint: disable=expression-not-assigned
    output | beam.io.WriteToPubSub(known_args.output_topic)


if __name__ == '__main__':
  logging.getLogger().setLevel(logging.INFO)
  run()