import json
import boto3
import hashlib
import os

#Database Functions
def save_connectionid_and_username (connectionid, username, dynamodb):
    try:
        dynamodb.put_item (
        TableName = os.environ['WEBSOCKET_TABLE'],
        Item = {
            'connectionid' : {'S' : connectionid},
            'username' : {'S': username}
            }
        )
    except Exception as e:
        raise e
    
def load_connectionid_and_username (dynamodb):
    try:
        paginator = dynamodb.get_paginator('scan')
        
        connectionids_to_usernames = {}
        for page in paginator.paginate(TableName=os.environ['WEBSOCKET_TABLE']):
            items = page.get('Items', [])
            for item in items: 
                connectionid = item.get('connectionid', {}).get('S')
                username = item.get('username', {}).get('S')
                connectionids_to_usernames[connectionid] = username
            
        return connectionids_to_usernames
    except Exception as e:
        raise e
    
def delete_connectionid_and_username (connectionid, dynamodb):
    try:
        dynamodb.delete_item(
            TableName = os.environ['WEBSOCKET_TABLE'],
            Key = {
                'connectionid' : {'S': connectionid}
            }
        )
    except Exception as e:
        raise e
    
#API Functions
def send_PublicMsg_Helper(endpoint, ids, message):
    for id in ids:
        send_PublicMsg(endpoint, id, message)
    
def send_PublicMsg(endpoint, connectionId, message):
    client = boto3.client('apigatewaymanagementapi', endpoint_url=endpoint)
    try:
        response = client.post_to_connection(
        ConnectionId=connectionId,
        Data=json.dumps(message).encode('utf-8')
        )
    except Exception as e:
        raise e

#Routing Function (Mini Backend Server)
def lambda_handler(event, context):
    #URL to connect to the websocket to send user and system messages to client
    endpoint = "https://" + event["requestContext"]["domainName"] + "/" + event["requestContext"]["stage"]
    #Database to save usernames and connectionids for each session
    dynamodb = boto3.client('dynamodb')
    
    #If there is a request sent for connection, extract the origin id and route
    if event.get("requestContext"):
        requestContext = event.get("requestContext") 
        
        connectionId = requestContext.get("connectionId")
        routeKey = requestContext.get("routeKey")
        
        body = {}
        if 'body' in event:
            try:
                body = json.loads(event['body'])
            except json.JSONDecodeError as e:
                raise e
        
        #Deal with routes
        if routeKey == '$connect':
            pass
        elif routeKey == '$disconnect':
            connectionids_to_usernames = load_connectionid_and_username(dynamodb)
            disconnected_username = connectionids_to_usernames[connectionId]
            delete_connectionid_and_username(connectionId, dynamodb)
            del connectionids_to_usernames[connectionId]
            
            
            send_PublicMsg_Helper(endpoint, connectionids_to_usernames.keys(), {'sys_message': f'{disconnected_username} has left the chat!'} )
            send_PublicMsg_Helper(endpoint, connectionids_to_usernames.keys(), {'members': list(connectionids_to_usernames.values())} )
    
        elif routeKey == 'setUsername':
            save_connectionid_and_username(connectionId, body['name'], dynamodb)
            connectionids_to_usernames = load_connectionid_and_username(dynamodb)
            
            send_PublicMsg_Helper(endpoint, connectionids_to_usernames.keys(), {'sys_message': f'{connectionids_to_usernames[connectionId]} has joined the chat! Say Hello!'} )
            send_PublicMsg_Helper(endpoint, connectionids_to_usernames.keys(), {'members': list(connectionids_to_usernames.values())} )
            
        elif routeKey == 'sendPublicMsg':
            connectionids_to_usernames = load_connectionid_and_username(dynamodb)
            
            send_PublicMsg_Helper(endpoint, connectionids_to_usernames.keys(), {'message': f'{connectionids_to_usernames[connectionId]}: {body['message']}'} )

        elif routeKey == '$default':
            pass
        
    return { 'statusCode': 200, 'body': json.dumps({'message': 'OK'})}
