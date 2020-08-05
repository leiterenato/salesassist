import argparse
import logging
import json
import re
import unittest

import apache_beam as beam
from apache_beam.testing import test_pipeline
from apache_beam.testing.util import assert_that
from apache_beam.testing.util import equal_to


# Tests:
# 1) Assert input equal expected output
# 2) Empty input
# 3) Input different than table_schema
# 4) JSON parse fail
# 5) Insert to BigQuery Fail

class TestJsonParsing(unittest.TestCase):
    def test_json_good_parsing(self):
        # Test if a good formed JSON is parsed
        # Json payload is good and match BQ Table Schema
        json_ok = [b'{"meetingid":"aaa-bbb-ccc", "transcription":"hi",'\
            b'"timestamp_transcription":"2020-08-24 12:44:31.744957 UTC"}']

        # Expected Dictionary        
        expected_json_ok = {"meetingid":"aaa-bbb-ccc", "transcription":"hi",
            "timestamp_transcription":"2020-08-24 12:44:31.744957 UTC"}

        with test_pipeline.TestPipeline() as p:
            input = p | beam.Create(json_ok)
            output = (input | beam.ParDo(ParseJson())
                                .with_outputs('json_decode_error', 
                                        main='cleared_json'))

            json_cleared = output.cleared_json
            assert_that(json_cleared, equal_to([expected_json_ok]))

    def test_json_bad_parsing(self):
        # Test if a bad formed JSON is parsed
        # Bad Json payload
        json_bad = [b'{meetingid":"aaa-bbb-ccc", "transcription":"oi",'\
            b'"timestamp_transcription":"2020-08-24 12:44:31.744957 UTC"}']
        
        expected_json_bad = {'meetingid': 'aaa-bbb-ccc', 
                            'payload': 'b\'{meetingid":"aaa-bbb-ccc", "transcription":"oi",'\
                                '"timestamp_transcription":"2020-08-24 12:44:31.744957 UTC"}\'', 
                            'error': 'JSONDecodeError: Expecting property name '\
                                'enclosed in double quotes: line 1 column 2 (char 1)'}

        with test_pipeline.TestPipeline() as p:
            input = p | beam.Create(json_bad)
            output = (input | beam.ParDo(ParseJson())
                                .with_outputs('json_decode_error', 
                                    main='cleared_json'))

            json_error = output.json_decode_error
            assert_that(json_error, equal_to([expected_json_bad]))


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
            error_message = {'meetingid':meeting, 
                            'payload':str(element), 
                            'error': e.__class__.__name__ + ': ' + str(e)}
            yield beam.pvalue.TaggedOutput('json_decode_error', error_message)
        else:
            yield element


# def run_pipeline(known_args=None, pipeline_args=None):

#     assert_that(
#         output,
#         equal_to(["elem1", "elem3", "elem2"]))

#     # Json payload is good and match BQ Table Schema
#     json_ok_insert_ok = [
#         b'{"meetingid":"aaa-bbb-ccc", "transcription":"oi", "timestamp_transcription":"2020-08-24 12:44:31.744957 UTC"}']
    
#     # Bad Json payload
#     json_bad = [
#         b'{meetingid":"aaa-bbb-ccc", "transcription":"oi", "timestamp_transcription":"2020-08-24 12:44:31.744957 UTC"}',
#         b'{meetingid":"aaa-bbb-ccc", "transcription":"oi"}']
    
#     # Json payload is good but don't match BQ Table Schema
#     json_ok_insert_bad = [b'{"meetingid":"aaa-bbb-ccc", "transcription":"oi"}']
    
#     # Define and run pipeline
#     with test_pipeline.TestPipeline() as p:
#         messages = (
#             p
#             | 'Read from Local Variable' >> 
#                 beam.io.ReadFromPubSub(subscription=known_args.input_subscription)
#                     .with_output_types(bytes)
#             | 'ParseJson' >> beam.ParDo(ParseJson())
#                     .with_outputs('json_decode_error', main='cleared_json'))

#         json_error =  messages.json_decode_error
#         json_cleared = messages.cleared_json

#         json_error | 'Write Errors to BigQuery' >> beam.io.WriteToBigQuery(
#                         known_args.output_error_bigquery,
#                         schema=TablesProperties.error_schema,
#                         create_disposition=beam.io.BigQueryDisposition.CREATE_IF_NEEDED,
#                         write_disposition=beam.io.BigQueryDisposition.WRITE_APPEND)

#         insert_errors = json_cleared | 'WritePayloadBigQuery' >> beam.io.WriteToBigQuery(
#                             known_args.output_bigquery,
#                             schema=TablesProperties.table_schema,
#                             insert_retry_strategy='RETRY_ON_TRANSIENT_ERROR',
#                             validate=False,
#                             create_disposition=beam.io.BigQueryDisposition.CREATE_NEVER,
#                             write_disposition=beam.io.BigQueryDisposition.WRITE_APPEND)

#         insert_result = (
#             insert_errors['FailedRows'] | 'WrapInsertionError' >> beam.ParDo(WrapInsertionError())
#                 | 'WriteInsertionErrorBigQuery' >> beam.io.WriteToBigQuery(
#                             known_args.output_error_bigquery,
#                             schema=TablesProperties.error_schema,
#                             insert_retry_strategy='RETRY_ON_TRANSIENT_ERROR',
#                             validate=False,
#                             create_disposition=beam.io.BigQueryDisposition.CREATE_NEVER,
#                             write_disposition=beam.io.BigQueryDisposition.WRITE_APPEND)
#             )


# class TablesProperties:
#     table_schema = {
#         'fields': [{
#             'name': 'meetingid', 'type': 'STRING', 'mode': 'REQUIRED'
#         }, {
#             'name': 'timestamp_transcription', 'type': 'TIMESTAMP', 'mode': 'REQUIRED'
#         }, {
#             'name': 'transcription', 'type': 'STRING', 'mode': 'REQUIRED'
#         }]
#     }

#     error_schema = {
#         'fields': [{
#             'name': 'meetingid', 'type': 'STRING', 'mode': 'NULLABLE'
#         }, {
#             'name': 'payload', 'type': 'STRING', 'mode': 'NULLABLE'
#         }, {
#             'name': 'error', 'type': 'STRING', 'mode': 'NULLABLE'
#         }]
#     }


# class WrapInsertionError(beam.DoFn):
#     def process(self, element):
#         meeting = re.search('[a-z]+-[a-z]+-[a-z]+', str(element[1]))
#         if meeting:
#             meeting = meeting.group()
#         else:
#             meeting = ''
#         error_message = {'meetingid':meeting, 'payload':str(element), 'error':'bigquery_insertion_error'}
#         yield error_message


# class PrintPayload(beam.DoFn):
#     def process(self, element):
#         print(element)
#         yield element


if __name__ == '__main__':
    unittest.main()
