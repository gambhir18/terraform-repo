
from __future__ import print_function
import json
import boto3
import logging
import time
import datetime

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    logger.info('################  Event: ############## ' + str(event))
    #print('Received event: ' + json.dumps(event, indent=2))

    ids = []

    try:
        region = event['region']
        detail = event['detail']
        eventname = detail['eventName']
        arn = detail['userIdentity']['arn']
        principal = detail['userIdentity']['principalId']
        userType = detail['userIdentity']['type']

        if userType == 'IAMUser':
            user = detail['userIdentity']['userName']

        else:
            user = principal.split(':')[1]


        logger.info('principalId: ' + str(principal))
        logger.info('region: ' + str(region))
        logger.info('eventName: ' + str(eventname))
        logger.info('detail: ' + str(detail))

        ec2_client = boto3.resource('ec2')
        lambda_client = boto3.client('lambda')
        rds_client = boto3.client('rds')
        s3_client = boto3.resource('s3')
        ddb_client = boto3.client('dynamodb')
        efs_client = boto3.client('efs')

        if eventname == 'CreateVolume':
            ids.append(detail['responseElements']['volumeId'])
            logger.info(ids)

        elif eventname == 'RunInstances' or eventname == 'StartInstances':
            items = detail['responseElements']['instancesSet']['items']
            for item in items:
                ids.append(item['instanceId'])
            logger.info(ids)
            logger.info('number of instances: ' + str(len(ids)))

            base = ec2_client.instances.filter(InstanceIds=ids)

            #loop through the instances
            for instance in base:
                for vol in instance.volumes.all():
                    ids.append(vol.id)
                for eni in instance.network_interfaces:
                    ids.append(eni.id)

        elif eventname == 'CreateImage':
            ids.append(detail['responseElements']['imageId'])
            logger.info(ids)

        elif eventname == 'CreateSnapshot':
            ids.append(detail['responseElements']['snapshotId'])
            logger.info(ids)

        elif eventname == 'CreateFunction20150331':
            try:
                functionArn = detail['responseElements']['functionArn']
                lambda_client.tag_resource(Resource=functionArn,Tags={'CreatedBy': user})
                lambda_client.tag_resource(Resource=functionArn,Tags={'DateCreated': time.strftime("%B %d %Y")})
            except Exception as e:
                logger.error('Exception thrown at CreateFunction20150331' + str(e))
                pass
        elif eventname == 'UpdateFunctionConfiguration20150331v2':
            try:
                functionArn = detail['responseElements']['functionArn']
                lambda_client.tag_resource(Resource=functionArn,Tags={'LastConfigModifiedByNetID': user})
            except Exception as e:
                logger.error('Exception thrown at UpdateFunctionConfiguration20150331v2' + str(e))
                pass
        elif eventname == 'UpdateFunctionCode20150331v2':
            try:
                functionArn = detail['responseElements']['functionArn']
                lambda_client.tag_resource(Resource=functionArn,Tags={'LastCodeModifiedByNetID': user})
            except Exception as e:
                logger.error('Exception thrown at UpdateFunctionCode20150331v2' + str(e))
                pass
        elif eventname == 'CreateDBInstance':
            try:
                dbResourceArn = detail['responseElements']['dBInstanceArn']
                rds_client.add_tags_to_resource(ResourceName=dbResourceArn,Tags=[{'Key':'CreatedBy','Value': user}])
            except Exception as e:
                logger.error('Exception thrown at CreateDBInstance' + str(e))
                pass
        elif eventname == 'CreateBucket':
            try:
                bucket_name = detail['requestParameters']['bucketName']
                s3_client.BucketTagging(bucket_name).put(Tagging={'TagSet': [{'Key':'CreatedBy','Value': user}]})
            except Exception as e:
                logger.error('Exception thrown at CreateBucket' + str(e))
                pass
        elif eventname == 'CreateTable':
            try:
                tableArn = detail['responseElements']['tableDescription']['tableArn']
                ddb_client.tag_resource(ResourceArn=tableArn,Tags=[{'Key':'CreatedBy','Value': user}])
            except Exception as e:
                logger.error('Exception thrown at CreateTable' + str(e))
                pass
        elif eventname == 'CreateMountTarget':
            try:
                system_id = detail['requestParameters']['fileSystemId']
                efs_client.create_tags(FileSystemId=system_id, Tags=[{'Key':'CreatedBy','Value': user}])
            except Exception as e:
                logger.error('Exception thrown at CreateMountTarget' + str(e))
                pass
        # todo: EMR and Glacier also possible candidates
        else:
            logger.warning('No matching eventname found in the Auto Tag lambda function (Ln 118)')

        if ids:
            for resourceid in ids:
                print('Tagging resource ' + resourceid)
                if 'Tags' in resourceid:
                    for tags in resourceid['Tags']:
                        if tags["Key"] == 'CreatedBy':
                            print('Tagging is already present on resource ' + tags)
                        else:
                            ec2_client.create_tags(Resources=ids, Tags=[{'Key': 'CreatedBy', 'Value': user}])

        logger.info(' Remaining time (ms): ' + str(context.get_remaining_time_in_millis()) + '\n')
        return True
    except Exception as e:
        logger.error('Something went wrong: ' + str(e))
        return False
