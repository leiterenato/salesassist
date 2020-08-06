import argparse
import logging
import json
import time
import datetime
import unittest

import apache_beam as beam
from apache_beam.io import fileio
from apache_beam.testing import test_pipeline
from apache_beam.testing.util import assert_that
from apache_beam.testing.util import equal_to


class TestBatchStorage(unittest.TestCase):
    def test_get_key(self):
        # Test if is returning meetingid correctly
        # Payload from BigQuery
        payload = {"meetingid":"aaa-bbb-ccc", "transcription":"hi",
            "timestamp_transcription":"2020-08-24 12:44:31.744957 UTC"}

        expected_output = ('aaa-bbb-ccc', payload)

        with test_pipeline.TestPipeline() as p:
            output = (p
                | beam.Create([payload])
                | beam.Map(lambda elem: (elem['meetingid'], elem)))

            assert_that(output, equal_to([expected_output]))

    def test_group_by_key(self):
        # Test if is returning meetingid correctly
        # Payload from BigQuery
        payload = {"meetingid":"aaa-bbb-ccc", "transcription":"hi",
            "timestamp_transcription":"2020-08-24 12:44:31.744957 UTC"}

        input_payload = [('aaa-bbb-ccc', payload), 
                        ('aaa-bbb-ccc', payload),
                        ('ddd-eee-fff', payload)]

        expected_output = [('aaa-bbb-ccc', [{'meetingid': 'aaa-bbb-ccc', 
                            'transcription': 'hi', 'timestamp_transcription': 
                            '2020-08-24 12:44:31.744957 UTC'}, {'meetingid': 
                            'aaa-bbb-ccc', 'transcription': 'hi', 
                            'timestamp_transcription': 
                            '2020-08-24 12:44:31.744957 UTC'}]),
                            ('ddd-eee-fff', [{'meetingid': 'aaa-bbb-ccc', 
                            'transcription': 'hi', 'timestamp_transcription': 
                            '2020-08-24 12:44:31.744957 UTC'}])]

        with test_pipeline.TestPipeline() as p:
            output = (p
                | beam.Create(input_payload)
                | beam.GroupByKey())

            assert_that(output, equal_to(expected_output))


    def test_empty_none_group_by_key(self):
        # Test if is returning meetingid correctly
        # Payload from BigQuery
        payload = ''

        input_payload = [(None, payload), 
                        ('', payload),
                        ('a', payload)]

        expected_output = [(None, ['']), ('', ['']), ('a', [''])]

        with test_pipeline.TestPipeline() as p:
            output = (p
                | beam.Create(input_payload)
                | beam.GroupByKey())

        assert_that(output, equal_to(expected_output))


class TestWritetoFiles(unittest.TestCase):
    def test_write_good_payload_file(self):

        input_payload = [('aaa-bbb-ccc', [{'meetingid': 'aaa-bbb-ccc', 
                            'transcription': 'hi', 'timestamp_transcription': 
                            '2020-08-24 12:44:31.744957 UTC'}, {'meetingid': 
                            'aaa-bbb-ccc', 'transcription': 'hi', 
                            'timestamp_transcription': 
                            '2020-08-24 12:44:31.744957 UTC'}]),
                        ('ddd-eee-fff', [{'meetingid': 'aaa-bbb-ccc', 
                            'transcription': 'hi', 'timestamp_transcription': 
                            '2020-08-24 12:44:31.744957 UTC'}])]

        day = datetime.date.today() - datetime.timedelta(days=1)
        day = day.strftime('%Y-%m-%d')
        expected_output = [day + '/aaa-bbb-ccc.json',
                           day + '/ddd-eee-fff.json']

        with test_pipeline.TestPipeline() as p:
            output = (p
                | beam.Create(input_payload)
                | fileio.WriteToFiles(
                    path='gs://salesassist-history',
                    destination=lambda element: element[0],
                    sink=lambda dest: JsonSink(),
                    file_naming=payload_naming)
                | beam.ParDo(TestGetFilename()))

            assert_that(output, equal_to(expected_output))


    def test_write_bad_payload_file(self):
        input_payload = [('', [{'meetingid': 'aaa-bbb-ccc', 
                            'transcription': 'hi', 'timestamp_transcription': 
                            '2020-08-24 12:44:31.744957 UTC'}, {'meetingid': 
                            'aaa-bbb-ccc', 'transcription': 'hi', 
                            'timestamp_transcription': 
                            '2020-08-24 12:44:31.744957 UTC'}]),
                        ('ddd-eee-fff', [{'meetingid': 'aaa-bbb-ccc', 
                            'transcription': 'hi', 'timestamp_transcription': 
                            '2020-08-24 12:44:31.744957 UTC'}])]

        day = datetime.date.today() - datetime.timedelta(days=1)
        day = day.strftime('%Y-%m-%d')
        expected_output = [day + '/.json',
                           day + '/ddd-eee-fff.json']

        with test_pipeline.TestPipeline() as p:
            output = (p
                | beam.Create(input_payload)
                | fileio.WriteToFiles(
                    path='gs://salesassist-history',
                    destination=lambda element: element[0],
                    sink=lambda dest: JsonSink(),
                    file_naming=payload_naming)
                | beam.ParDo(TestGetFilename()))

            assert_that(output, equal_to(expected_output))


class TestGetFilename(beam.DoFn):
    def process(self, element):
        yield(element.file_name)


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
    unittest.main()