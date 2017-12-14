from __future__ import unicode_literals
import youtube_dl
import os, os.path
import boto3
import re
import glob

client = boto3.client('s3')
bucket = 'localize-mp3'

def remove_files():
	filelist = glob.glob(os.path.join('/tmp', "*.mp3"))
	for f in filelist:
		os.remove(f)

def get_mp3():
	return filter(lambda file: re.match('.*\.mp3$', file), os.listdir('/tmp'))[0]

def upload(d, phone_number=0):
	filename = "{0}.mp3".format(str(d['title']))
	filepath = "/tmp/{0}".format(get_mp3())
	client.upload_file(filepath, bucket, filename, ExtraArgs={'ContentType': 'audio/mp3', "Metadata" : {'phone_number': phone_number}})
	region = "us-east-1"
	remove_files()
	return "https://s3-%s.amazonaws.com/{0}/{1}".format(region, bucket, filename)

def lambda_handler(event, context):
	url = event['Records'][0]['Sns']['MessageAttributes']['url']['Value']
	phone_number = event['Records'][0]['Sns']['MessageAttributes']['phone_number']['Value']
	ydl_opts = {
		'outtmpl': '/tmp/%(title)s.%(ext)s',
		'format': 'bestaudio/best',
  }
	ydl = youtube_dl.YoutubeDL(ydl_opts)
	ydl.add_default_info_extractors()
	info = ydl.extract_info(url)
	return upload(info, phone_number)