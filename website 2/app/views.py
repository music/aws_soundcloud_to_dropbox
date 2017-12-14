from app import app
from flask import render_template, request, redirect
import requests as r
import json
import re
import boto3
from boto3.dynamodb.conditions import Key
from twilio.twiml.messaging_response import MessagingResponse
from info import APP_KEY, APP_SECRET, REDIRECT_URI, TOPIC_ARN

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('Users')

@app.route('/')
def home():
  return render_template('home.html',
                          app_key=APP_KEY,
                          redirect_uri=REDIRECT_URI,
                          logged_in=False)

@app.route('/profile')
def profile():
  if request.args.get('code'):
    code = request.args.get('code')
    print code
    data = {
      'code': code,
      'grant_type': 'authorization_code',
      'client_id': APP_KEY,
      'client_secret': APP_SECRET,
      'redirect_uri': REDIRECT_URI
    }
    resp = r.post('https://api.dropboxapi.com/oauth2/token', data=data)
    print resp.json()
    access_token = resp.json()['access_token']
    account_id = resp.json()['account_id']

    response = table.get_item(
      Key={
        'account_id': account_id
      }
    )
    phone_number = None
    if 'Item' in response:
      phone_number = response['Item']['phone_number']
      table.update_item(
        Key={
          'account_id': account_id
        },
        UpdateExpression='SET dropbox_key = :key',
        ExpressionAttributeValues={
          ':key': access_token
        }
      )
    else:
      table.put_item(
        Item={
          'account_id': account_id,
          'dropbox_key': access_token
        }
      )
    return render_template('profile.html',
                            account_id=account_id,
                            phone_number=phone_number)
  else:
    return redirect('/error')

@app.route('/save_phone_number')
def save_phone_number():
  phone_number = request.args.get('number')
  account_id = request.args.get('account_id')
  print phone_number
  print account_id

  if phone_number:
    table.update_item(
      Key={
        'account_id': account_id
      },
      UpdateExpression='SET phone_number = :number',
      ExpressionAttributeValues={
        ':number': phone_number
      }
    )

    return render_template('profile.html',
                            saved=True,
                            account_id=account_id,
                            phone_number=phone_number)
  else:
    return render_template('profile.html',
                            error=True,
                            account_id=account_id)

@app.route("/download", methods=['POST'])
def incoming():
  phone_number = request.values.get('From', None)
  resp = MessagingResponse()
  response = table.query(
    IndexName='phone_number-index',
    KeyConditionExpression=Key('phone_number').eq(phone_number[2:])
  )
  if len(response['Items']) == 0:
    resp.message('This is an unregistered or corrupted number!')
    return str(resp)
  
  url = request.values.get('Body', None)
  
  if not re.search(r'soundcloud\.com\/.+\/.+$', url):
    resp.message('This is not a valid link!')
    return str(resp)
  
  client = boto3.client("sns")
  r = client.publish(
      TopicArn=TOPIC_ARN,
      Message='string',
      MessageAttributes={
          'url': {
            'DataType': 'String',
            'StringValue': url
          },
          'phone_number': {
            'DataType': 'Number',
            'StringValue': str(response['Items'][0]['phone_number'])
          }
      }
  )
  resp.message('Attempting to download!')
  return str(resp)


@app.route('/error')
def error():
  return render_template('error.html')  

# old color: 1E90FF