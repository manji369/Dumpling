import random
from textblob import TextBlob
import nltk
from boto.s3.connection import S3Connection

def parseInt(value):
    try:
        return int(value)
    except ValueError:
        return 100


def dumpler(event, context):
    print(event)
    intent = event['request']['type']
    if intent == u'LaunchRequest':
        return build_response("Hi there. How was you day?", False)
    textInput = None
    intentName = event['request']['intent']['name']
    if intentName == 'DiaryInput':
        conn = S3Connection('aws access key', 'aws secret key')
        bucket = conn.get_bucket('hackazdailydiary')
        key = bucket.get_key('log.txt')
        key.get_contents_to_filename('/tmp/log.txt')
        textInput = event['request']['intent']['slots']['TextInput']
        if 'value' in textInput:
            textInput = str(textInput['value'])
            blob = TextBlob(textInput)
            pol = 0
            for sentence in blob.sentences:
                pol += sentence.sentiment.polarity
            day_type = 'rough'
            if pol > 0:
                day_type = 'good'
            with open('/tmp/log.txt') as f:
                cont = f.read().strip()
            if cont:
                pols = cont.split(',')
                pols.append(str(pol))
                if len(pols) > 7:
                    del pols[0]
                cont = ','.join(pols)
            else:
                cont = str(pol)
            print(cont)
            key = bucket.new_key('log.txt')
            key.set_contents_from_string(cont)
            key.set_acl('public-read')
            text = 'I heard ' + textInput + '? If so, I think you had a ' + day_type + 'day. '
            if day_type == 'good':
                text += 'Take rest and keep up this good spirit.'
            else:
                text += random.choice(['Go out and watch a movie. The greatest showman is in theatres.',
                'Go talk to a friend or family',
                'Go out and watch a movie. Paddington two is in theatres and has 100 percentage on rotten tomatoes.',
                'I think you should watch the tv series Big bang theory. Its hilarious. You will love it.',
                'Cheer up <audio src="https://s3.amazonaws.com/mp3filesmanjit/baby0.mp3"/>',
                'Cheer up <audio src="https://s3.amazonaws.com/mp3filesmanjit/baby1.mp3"/>',
                'Cheer up <audio src="https://s3.amazonaws.com/mp3filesmanjit/baby2.mp3"/>'
                ])
                # text += 'Heres a cute baby voice for you <audio src="https://s3.amazonaws.com/mp3filesmanjit/baby0.mp3"/>'
            return build_response(text)
    else:
        conn = S3Connection('AKIAJP5VDW25FH3WTBOA', 'jeivL76cKkPnN2MZGx0HlrPqPqaRCTGcLkzqay5q')
        bucket = conn.get_bucket('hackazdailydiary')
        key = bucket.get_key('log.txt')
        key.get_contents_to_filename('/tmp/log.txt')
        with open('/tmp/log.txt') as f:
            cont = f.read().strip()
        week_type = 'good'
        if cont:
            past_results = [float(x) for x in cont.split(',')]
            avg = sum(past_results)/len(past_results)
            if avg < 0:
                week_type = 'rough'
        text = 'You had a ' + week_type + ' week. Take a look at the app for your mood chart. '
        if week_type == 'good':
            text += 'Take rest and keep up this good spirit.'
        else:
            text += random.choice(['Go out and watch a movie. The greatest showman is in theatres.',
            'Go talk to a friend or family',
            'Go out and watch a movie. Paddington two is in theatres and has 100 percentage on rotten tomatoes.',
            'I think you should watch the tv series Big bang theory. Its hilarious. You will love it.',
            'Cheer up <audio src="https://s3.amazonaws.com/mp3filesmanjit/baby0.mp3"/>',
            'Cheer up <audio src="https://s3.amazonaws.com/mp3filesmanjit/baby1.mp3"/>',
            'Cheer up <audio src="https://s3.amazonaws.com/mp3filesmanjit/baby2.mp3"/>'
            ])
            # text += 'Heres a cute baby voice for you. <audio src="https://s3.amazonaws.com/mp3filesmanjit/baby0.mp3"/>'
        return build_response(text)

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
