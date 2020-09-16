import argparse
import logging
import json
import time
import datetime

import apache_beam as beam
from apache_beam.io import fileio

from apache_beam.options.pipeline_options import PipelineOptions
from apache_beam.options.pipeline_options import SetupOptions
from apache_beam.options.pipeline_options import StandardOptions
from apache_beam.options.pipeline_options import GoogleCloudOptions


def run():
    pipeline_options = PipelineOptions()
    pipeline_options.view_as(StandardOptions).runner = 'DataflowRunner'
    pipeline_options.view_as(SetupOptions).save_main_session = True

    pipeline_options.view_as(GoogleCloudOptions).project = 'cool-ml-demos'
    pipeline_options.view_as(GoogleCloudOptions).temp_location = 'gs://salesassist-history/tmp/'
    pipeline_options.view_as(GoogleCloudOptions).region = 'us-east1'

    query = 'SELECT * FROM `cool-ml-demos.salesassist.history` '\
            'WHERE EXTRACT(DATE FROM start) > '\
            'EXTRACT(DATE FROM TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY))'

    with beam.Pipeline(options=pipeline_options) as p:
        messages = (
            p
             | 'Read from Bigquery' >> beam.io.Read(beam.io.BigQuerySource(
                                            query = query, use_standard_sql=True))
             | 'Get Key' >> beam.Map(lambda elem: (elem['uid'] + '-' + elem['meetingid'], elem))
             | 'Group by MeetingID' >> beam.GroupByKey()
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
    d1 = datetime.date.today()
    d1 = d1.strftime('%Y-%m-%d')
    return 'archive/{}/{}.json'.format(d1, args[5])


if __name__ == '__main__':
    logging.getLogger().setLevel(logging.INFO)
    run()