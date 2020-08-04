from __future__ import absolute_import

import argparse
import logging
import json
import time
import datetime

from past.builtins import unicode

import apache_beam as beam
from apache_beam.io import fileio


def run(argv=None, save_main_session=True):
    """Build and run the pipeline."""

    parser = argparse.ArgumentParser(prog='Assist Archive')
    known_args, pipeline_args = parser.parse_known_args(argv)

    # We use the save_main_session option because one or more DoFn's in this
    # workflow rely on global context (e.g., a module imported at module level).

    query = 'SELECT * FROM `cool-ml-demos.salesassist.history` '\
            'WHERE EXTRACT(DATE FROM timestamp_transcription) = '\
            'EXTRACT(DATE FROM TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 DAY))'

    with beam.Pipeline(argv=pipeline_args) as p:
        messages = (
            p
             | 'Read from Bigquery' >> beam.io.Read(beam.io.BigQuerySource(
                                            query = query, use_standard_sql=True))
             | 'Get Key' >> beam.Map(lambda elem: (elem['meetingid'], elem))
             | 'Group by MeetingID' >> beam.GroupByKey()
            #  | 'List of Grouped Elements' >> beam.MapTuple(lambda _, val: (list(val))
            #  | 'Newline Delimited JSON' >> beam.ParDo(NewlineDelimitedJSON())
            #  | 'Print Elements' >> beam.Map(lambda element: print(element[0], list(element[1])))
            #  | 'Print Tuple' >> beam.ParDo(NewlineDelimitedJSON())
             | 'Write to Bucket' >> fileio.WriteToFiles(
                                        path='gs://salesassist-history',
                                        destination=lambda element: element[0],
                                        sink=lambda dest: JsonSink(),
                                        file_naming=payload_naming)
        )


class JsonSink(fileio.TextSink):
    def write(self, element):
        element = [json.dumps(i) for i in element[1]]
        element = '\n'.join(element).encode('utf8')
        self._fh.write(element)


def payload_naming(*args):
    d1 = datetime.date.today() - datetime.timedelta(days=1)
    d1 = d1.strftime('%Y-%m-%d')
    return '{}/{}.json'.format(d1, args[5])


if __name__ == '__main__':
    logging.getLogger().setLevel(logging.INFO)
    run()