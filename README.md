blackbird-dynamodb
==================

Get DynamoDB CloudWatch Metrics.


What metrics this script get?
-----------------------------

### Table Metrics

| Metric Name                   | Statistics Type |
|-------------------------------|-----------------|
| UserErrors                    | Sum             |
| SystemErrors                  | Sum             |
| ThrottledRequests             | Sum             |
| ReadThrottleEvents            | Sum             |
| WriteThrottleEvents           | Sum             |
| ProvisionedReadCapacityUnits  | Maximum         |
| ProvisionedWriteCapacityUnits | Maximum         |
| ConsumedReadCapacityUnits     | Maximum         |
| ConsumedReadCapacityUnits     | Average         |
| ConsumedWriteCapacityUnits    | Maximum         |
| ConsumedWriteCapacityUnits    | Average         |

### Each Operation Metrics

| Operation Name | Metric Name              | Statistics Type |
|----------------|--------------------------|-----------------|
| PutItem        | SuccessfulRequestLatency | Maximum         |
| PutItem        | SuccessfulRequestLatency | Average         |
| DeleteItem     | SuccessfulRequestLatency | Maximum         |
| DeleteItem     | SuccessfulRequestLatency | Average         |
| UpdateItem     | SuccessfulRequestLatency | Maximum         |
| UpdateItem     | SuccessfulRequestLatency | Average         |
| GetItem        | SuccessfulRequestLatency | Maximum         |
| GetItem        | SuccessfulRequestLatency | Average         |
| BatchGetItem   | SuccessfulRequestLatency | Maximum         |
| BatchGetItem   | SuccessfulRequestLatency | Average         |
| BatchWriteItem | SuccessfulRequestLatency | Maximum         |
| BatchWriteItem | SuccessfulRequestLatency | Average         |
| Scan           | SuccessfulRequestLatency | Maximum         |
| Scan           | SuccessfulRequestLatency | Average         |
| Scan           | ReturnedItemCount        | Maximum         |
| Scan           | ReturnedItemCount        | Average         |
| Query          | SuccessfulRequestLatency | Maximum         |
| Query          | SuccessfulRequestLatency | Average         |
| Query          | ReturnedItemCount        | Maximum         |
| Query          | ReturnedItemCount        | Average         |


Configurations
--------------

| Kay Name                 | Default   | Type                        | Require | Notes                                       |
|--------------------------|-----------|-----------------------------|---------|---------------------------------------------|
| region\_name             | us-east-1 | str                         | No      | Region name                                 |
| aws\_access\_key\_id     | -         | str                         | Yes     | Your aws access key id                      |
| aws\_secret\_access\_key | -         | str                         | Yes     | Your aws secret access key                  |
| table\_name              | -         | str                         | Yes     | Your DynamoDB table name                    |
| hostname                 | -         | str                         | Yes     | Your hostname in zabbix server              |
| module                   | -         | str                         | Yes     | You must specify `dynamodb` to module name. |
| ignore\_metrics          | -         | str(comma-separated values) | No      | Ignore table metrics                        |
| ignore\_operations       | -         | str(comma-separated values) | No      | Ignore operations metrics                   |

### Notes

#### ignore\_metrics
If you don't want to get any metrics, you should use `ignore\_metrics` parameter. So, you can throttle request to AWS CloudWatch by using ignore\_metrics parameter.

e.g:

```
[DynamoDB.TABLE_NAME]
ignore_metrics = UserErrors, ReadThrottleEvents, WriteThrottleEvents
```

#### ignore\_operations
You may not use any operation. You would want to reduce futile requests to AWS CloudWatch in such situations. We recommend to use this parameter.

e.g:

```
[DynamoDB.TABLE_NAME]
ignore_operations = PutItem, DeleteItem, UpdateItem, GetItem, BatchGetItem
```

Above configurations shows that `blackbird` does not get `PutItem, DeleteItem, UpdateItem, GetItem, BatchGetItem` metrics.
