import boto3
import re
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from boto3.dynamodb.conditions import Key,Attr
from info import TOPIC_ARN

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('users')

app = Flask(__name__)

@app.route("/download", methods=['POST'])
def incoming():
	phone_number = request.values.get('From', None)
	response = table.scan(
	  FilterExpression=Attr('phone_number').eq(phone_number)
	)
	resp = MessagingResponse()
	if response['Count'] != 1:
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

if __name__ == "__main__":
	app.run(debug=True)