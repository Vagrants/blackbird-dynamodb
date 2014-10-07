#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Fetch DynamoDB metrics.
"""

import datetime

from boto.ec2 import cloudwatch

from blackbird.plugins import base


class ConcreteJob(base.JobBase):

    def __init__(self, options, queue=None, logger=None):
        super(ConcreteJob, self).__init__(options, queue, logger)
        self.table_metrics = [
            {'UserErrors': 'Sum'},
            {'SystemErrors': 'Sum'},
            {'ThrottledRequests': 'Sum'},
            {'ReadThrottleEvents': 'Sum'},
            {'WriteThrottleEvents': 'Sum'},
            {'ProvisionedReadCapacityUnits': 'Maximum'},
            {'ProvisionedWriteCapacityUnits': 'Maximum'},
            {'ConsumedReadCapacityUnits': 'Maximum'},
            {'ConsumedReadCapacityUnits': 'Average'},
            {'ConsumedWriteCapacityUnits': 'Maximum'},
            {'ConsumedWriteCapacityUnits': 'Average'},
        ]
        self.query_metrics = [
            {
                'PutItem': [
                    {'SuccessfulRequestLatency': 'Maximum'},
                    {'SuccessfulRequestLatency': 'Average'},
                ]
            },
            {
                'DeleteItem': [
                    {'SuccessfulRequestLatency': 'Maximum'},
                    {'SuccessfulRequestLatency': 'Average'},
                ]
            },
            {
                'UpdateItem': [
                    {'SuccessfulRequestLatency': 'Maximum'},
                    {'SuccessfulRequestLatency': 'Average'},
                ]
            },
            {
                'GetItem': [
                    {'SuccessfulRequestLatency': 'Maximum'},
                    {'SuccessfulRequestLatency': 'Average'},
                ]
            },
            {
                'BatchGetItem': [
                    {'SuccessfulRequestLatency': 'Maximum'},
                    {'SuccessfulRequestLatency': 'Average'},
                ]
            },
            {
                'BatchWriteItem': [
                    {'SuccessfulRequestLatency': 'Maximum'},
                    {'SuccessfulRequestLatency': 'Average'},
                ]
            },
            {
                'Scan': [
                    {'SuccessfulRequestLatency': 'Maximum'},
                    {'SuccessfulRequestLatency': 'Average'},
                    {'ReturnedItemCount': 'Maximum'},
                    {'ReturnedItemCount': 'Average'},
                ]
            },
            {
                'Query': [
                    {'SuccessfulRequestLatency': 'Maximum'},
                    {'SuccessfulRequestLatency': 'Average'},
                    {'ReturnedItemCount': 'Maximum'},
                    {'ReturnedItemCount': 'Average'},
                ]
            },
        ]

        self.period = int(self.options.get('interval', 300))
        if self.period <= 60:
            self.period = 60
            delta_seconds = 120
        else:
            delta_seconds = self.period * 2

        self.end_time = datetime.datetime.utcnow()
        self.start_time = self.end_time - datetime.timedelta(
            seconds=delta_seconds
        )

    def _enqueue(self, item):
        self.queue.put(item, block=False)
        self.logger.debug(
            'Inserted {key}:{value} to sending queue.'
            ''.format(
                key=item.data['key'],
                value=item.data['value']
            )
        )

    def _create_connection(self):
        conn = cloudwatch.connect_to_region(
            self.options.get('region_name'),
            aws_access_key_id=self.options.get('aws_access_key_id'),
            aws_secret_access_key=self.options.get('aws_secret_access_key')
        )
        return conn

    def _fetch_table_metrics(self, conn):
        result = dict()

        dimensions = {
            'TableName': self.options['table_name']
        }

        for entry in self.table_metrics:
            for metric_name, statistics in entry.iteritems():
                if not metric_name in self.options.get(
                    'ignore_metrics', list()
                ):
                    key = 'cloudwatch.dynamodb.{0}.{1}'.format(
                        metric_name,
                        statistics
                    )
                    value = conn.get_metric_statistics(
                        period=self.period,
                        start_time=self.start_time,
                        end_time=self.end_time,
                        metric_name=metric_name,
                        namespace='AWS/DynamoDB',
                        statistics=statistics,
                        dimensions=dimensions
                    )

                    if len(value) > 0:
                        result[key] = value[0][statistics]
                    else:
                        result[key] = None

        return result

    def _fetch_query_metrics(self, conn):
        result = dict()
        dimensions = {
            'TableName': self.options['table_name'],
        }

        for entry in self.query_metrics:
            for operation, element in entry.iteritems():
                if not operation in self.options.get(
                    'ignore_operations', list()
                ):
                    dimensions['Operation'] = operation
                    for metrics in element:
                        for metric_name, statistics in metrics.iteritems():
                            key = 'cloudwatch.dynamodb.{0}.{1}.{2}'.format(
                                operation,
                                metric_name,
                                statistics
                            )
                            value = conn.get_metric_statistics(
                                period=self.period,
                                start_time=self.start_time,
                                end_time=self.end_time,
                                metric_name=metric_name,
                                namespace='AWS/DynamoDB',
                                statistics=statistics,
                                dimensions=dimensions
                            )

                            if len(value) > 0:
                                result[key] = value[0][statistics]
                            else:
                                result[key] = None

        return result

    def _fetch_metrics(self):
        result = dict()
        conn = self._create_connection()
        result.update(
            self._fetch_table_metrics(conn)
        )
        result.update(
            self._fetch_query_metrics(conn)
        )
        result.update(
            self._build_ping_item()
        )
        return result

    def _build_ping_item(self):
        return {
            'blackbird.dynamodb.ping': 1
        }

    def build_items(self):
        """
        Main loop
        """
        raw_items = self._fetch_metrics()
        hostname = self.options.get('hostname')

        self.logger.info(
            'The number of metrics is {0}'.format(
                len(raw_items)
            )
        )

        for key, raw_value in raw_items.iteritems():

            if not (
                key.startswith('Provisioned') and raw_value is None
            ):
                if raw_value is None:
                    value = 0
                else:
                    value = raw_value

                item = DynamoDBItem(
                    key=key,
                    value=value,
                    host=hostname
                )
                self._enqueue(item)


class DynamoDBItem(base.ItemBase):

    def __init__(self, key, value, host):
        super(DynamoDBItem, self).__init__(key, value, host)

        self.__data = dict()
        self._generate()

    @property
    def data(self):
        return self.__data

    def _generate(self):
        self.__data['key'] = self.key
        self.__data['value'] = self.value
        self.__data['host'] = self.host
        self.__data['clock'] = self.clock


class Validator(base.ValidatorBase):

    def __init__(self):
        self.__spec = None

    @property
    def spec(self):
        self.__spec = (
            "[{0}]".format(__name__),
            "region_name = string(default='us-east-1')",
            "aws_access_key_id = string()",
            "aws_secret_access_key = string()",
            "table_name = string()",
            "hostname = string()",
            "ignore_operations = list(default=list())",
            "ignore_metrics = list(default=list())",
        )
        return self.__spec


if __name__ == '__main__':
    import json
    OPTIONS = {
        'region_name': 'us-esat-1',
        'aws_access_key_id': 'YOUR_AWS_ACCESS_KEY_ID',
        'aws_secret_access_key': 'YOUR_AWS_SECRET_ACCESS_KEY',
        'table_name': 'YOUR_TABLE_NAME',
        'ignore_operations': list(),
        'ignore_metrics': list(),
        'interval': 300
    }
    JOB = ConcreteJob(
        options=OPTIONS
    )
    print(json.dumps(JOB._fetch_metrics()))
