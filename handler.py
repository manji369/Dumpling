import random
from textblob import TextBlob
import nltk
import boto3
import datetime
import uuid
from boto3.dynamodb.conditions import Key, Attr
from decimal import *

def parseInt(value):
    try:
        return int(value)
    except ValueError:
        return 100

def connect_to_db():
    dynamodb = boto3.resource('dynamodb', region_name='us-west-1')
    table = dynamodb.Table('dumpling')
    return table

def get_uid(event):
    return event['session']['user']['userId']

def get_uuid():
    return str(uuid.uuid4())

def get_timestamp(timeframe=0):
    return (datetime.datetime.now() - datetime.timedelta(days=timeframe)).isoformat()

def get_polarity(textInput):
    blob = TextBlob(textInput)
    pol = 0
    for sentence in blob.sentences:
        pol += sentence.sentiment.polarity
    return pol

def classify_sentiment(pol):
    day_type = 'bad'
    if pol > 0:
        day_type = 'good'
    return day_type

def list_choices():
    list_choices = ['Go out and watch a movie. The greatest showman is in theatres.',
    'Go talk to a friend or family',
    'Go out and watch a movie. Paddington two is in theatres and has 100 percentage on rotten tomatoes.',
    'I think you should watch the tv series Big bang theory. Its hilarious. You will love it.',
    'Cheer up <audio src="https://s3.amazonaws.com/mp3filesmanjit/baby0.mp3"/>',
    'Cheer up <audio src="https://s3.amazonaws.com/mp3filesmanjit/baby1.mp3"/>',
    'Cheer up <audio src="https://s3.amazonaws.com/mp3filesmanjit/baby2.mp3"/>'
    ]
    return list_choices

def generate_text(textInput, label, dayOrWeek='day'):
    if dayOrWeek == 'day':
        text = 'I heard ' + textInput + '? If so, I think you had a ' + label + ' day. '
    else:
        text = 'You had a ' + label + ' week. '
    if label == 'good':
        text += 'Take rest and keep up this good spirit.'
    else:
        text += random.choice(list_choices())
    return text

def get_past_results(table, uid, timeframe=7):
    sentiments = []
    dt1 = get_timestamp()
    dt2 = get_timestamp(timeframe)
    filtering_exp = Key('uid').eq(uid) and Key('timestamp').between(dt2, dt1)
    response = table.scan(FilterExpression=filtering_exp)
    for item in response['Items']:
        sentiments.append(float(item['sentiment']))
    while 'LastEvaluatedKey' in response:
        response = table.scan(
            FilterExpression=filtering_exp,
            ExclusiveStartKey=response['LastEvaluatedKey']
            )
        for item in response['items']:
            sentiments.append(float(item['sentiment']))
    return sentiments

def process_help():
    return build_response('You can describe how your day was in a sentence or few.', False)

def process_stop():
    return build_response('Ok. Closing the skill.')

def process_day(textInput, uid, table, event):
    textInput = event['request']['intent']['slots']['TextInput']
    if 'value' in textInput:
        textInput = str(textInput['value'])
        if textInput.lower() == 'help':
            return process_help()
        elif textInput.lower() == 'stop' or textInput.lower() == 'cancel':
            return process_stop()
        pol = get_polarity(textInput)
        day_type = classify_sentiment(pol)
        text = generate_text(textInput, day_type)
        Item = {
                    'uuid': get_uuid(),
                    'uid': uid,
                    'text': textInput,
                    'sentiment': Decimal(str(pol)),
                    'label': day_type,
                    'timestamp': get_timestamp()
        }
        table.put_item(Item=Item)
        return build_response(text)
    else:
        return build_response('I could not hear anything', False)

def process_week(uid, table):
    past_results = get_past_results(table, uid)
    if len(past_results) == 0:
        return build_response("As of now, there are no entries recorded.")
    avg_pol = sum(past_results)/len(past_results)
    week_type = classify_sentiment(avg_pol)
    text = generate_text('', week_type, 'week')
    return build_response(text)

def dumpler(event, context):
    print(event)
    table = connect_to_db()
    uid = get_uid(event)
    intent = event['request']['type']
    if intent == u'LaunchRequest':
        return build_response("Hi there. How was you day?", False)
    textInput = None
    intentName = event['request']['intent']['name']
    if intentName == 'DiaryInput':
        return process_day(textInput, uid, table, event)
    else:
        return process_week(uid, table)

    return build_response('Sorry. I could not get that')

def build_response(resp_text, shouldEndSession=True):
    response = {
        'version': '1.0',
        'response': {
            'outputSpeech': {
                'type': 'SSML',
                'ssml': '<speak>' + resp_text + '</speak>'
            },
            'shouldEndSession': shouldEndSession
        }
    }
    return response
