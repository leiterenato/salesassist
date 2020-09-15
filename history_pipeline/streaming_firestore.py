import argparse
import logging
import json
import re

import apache_beam as beam
from google.cloud import firestore


def run_pipeline(known_args, pipeline_args):
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

        # Write JSON Decode error to Firestore
        json_error | 'JSON Errors Firestore' >> beam.ParDo(
            InsertJsonError())

        # Write and Get insertion errors from Firebase
        insert_errors = json_cleared | 'Write Payload Firebase' >> beam.ParDo(
            InsertFirestore()).with_outputs('error', main='insertion_ok')

        # Write errors from insertion
        insert_errors.error | 'Insertion Error to Firestore' >> beam.ParDo(
            InsertErrorFirestore())


class ParseJson(beam.DoFn):
    def process(self, element):
        try:
            element = json.loads(element)
        except ValueError as e:
            error_message = {'payload':str(element), 
                            'error':e.__class__.__name__ + ': ' + str(e)}
            yield beam.pvalue.TaggedOutput('json_decode_error', error_message)
        else:
            yield element


class InsertJsonError(beam.DoFn):
    def setup(self):
        try:
            self.db = firestore.Client()
        except:
            logging.info('Fail to create Client in InsertJsonError class')

    def process(self, element):
        try:
            # Set Collection JSON Errors
            self.col_ref = self.db.collection('json_errors')
            # Set Document with random key
            self.doc_ref = self.col_ref.document()
            self.doc_ref.set(element)
        except:
            logging.info('Failed to insert: InsertJsonError')


class InsertFirestore(beam.DoFn):
    def setup(self):
        try:
            self.db = firestore.Client()
        except:
            logging.info('Fail to create Client in InsertFirestore class')

    def process(self, element):
        try:
            # Set Collection Users
            self.col_ref = self.db.collection('users')

            if 'uid' in element and 'meetingid' in element:
                # Set Document for User with UID
                self.doc_ref = self.col_ref.document(element['uid'])               
            else:
                raise KeyError
            # Set Collections for Meetings
            self.subcol_ref = self.doc_ref.collection('meetings')
            # Set Meeting Document and insert element
            self.subdoc_ref = self.subcol_ref.document(element['meetingid'])
            self.subdoc_ref.set(element)
        except KeyError as e:
            if 'meetingid' in element:
                meeting = element['meetingid']
            else:
                meeting = 'meeting'
            if 'uid' in element:
                uid = element['uid']
            else:
                uid = 'uid'

            error_message = {'uid':uid,
                            'meetingid':meeting, 
                            'payload':str(element), 
                            'error':e.__class__.__name__ + ': ' + str(e)}
            yield beam.pvalue.TaggedOutput('error', error_message)
        else:
            yield element


class InsertErrorFirestore(beam.DoFn):
    def setup(self):
        try:
            self.db = firestore.Client()
        except:
            logging.info('Fail to create Client in InsertErrorFirestore class')

    def process(self, element):
        try:
            doc_name = element['uid'] + '-' + element['meetingid']
            # Set Collection Insertion Errors
            self.col_ref = self.db.collection('insertion_errors')
            # Set Document for User with UID
            self.doc_ref = self.col_ref.document(doc_name)
            self.doc_ref.set(element)
        except:
            logging.info('Failed to insert: InsertErrorFirestore')


if __name__ == '__main__':
    logging.getLogger().setLevel(logging.INFO)

    parser = argparse.ArgumentParser(prog='Assist Streaming for Firebase')
    parser.add_argument(
        '--input_subscription',
        dest='input_subscription',
        default='projects/cool-ml-demos/subscriptions/sales-assist-firestore',
        help='Input subscription')

    known_args, pipeline_args = parser.parse_known_args(None)
    run_pipeline(known_args, pipeline_args)
