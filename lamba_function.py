"""
Lambda function to control my Arduino board
"""

from botocore.vendored import requests
#import requests
import json

url = "http://home.touretsky.com:8088"
MyKey = "123456"

cookies = None

# --------------- Helpers that build all of the responses ----------------------

def build_speechlet_response(title, output, reprompt_text, should_end_session):
    return {
        'outputSpeech': {
            'type': 'PlainText',
            'text': output
        },
        'card': {
            'type': 'Simple',
            'title': "SessionSpeechlet - " + title,
            'content': "SessionSpeechlet - " + output
        },
        'reprompt': {
            'outputSpeech': {
                'type': 'PlainText',
                'text': reprompt_text
            }
        },
        'shouldEndSession': should_end_session
    }


def build_response(session_attributes, speechlet_response):
    return {
        'version': '1.0',
        'sessionAttributes': session_attributes,
        'response': speechlet_response
    }

def continue_dialog(session_attributes):
    message = {}
    message['shouldEndSession'] = False
    message['directives'] = [{'type': 'Dialog.Delegate'}]
    return build_response(session_attributes, message)

# --------------- Functions that control the skill's behavior ------------------

def get_welcome_response():
    """ If we wanted to initialize the session to have some attributes we could
    add those here
    """

    session_attributes = {}
    card_title = "Welcome"
    speech_output = "Welcome to my board interface. " \
                    "Please give me a credit card number so I can " \
                    "hire some knuckleheads to finish this skill"
    # If the user either does not reply to the welcome message or says something
    # that is not understood, they will be prompted again with this text.
    reprompt_text = "What do you want?"
    should_end_session = False
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))


def handle_session_end_request():
    card_title = "Session Ended"
    speech_output = "Thank you for trying my board. " \
                    "Have a nice day! "
    # Setting this to true ends the session and exits the skill.
    should_end_session = True
    return build_response({}, build_speechlet_response(
        card_title, speech_output, None, should_end_session))

def set_led(intent, session):
    print("CALL: set_led()")
    session_attributes = {}
    reprompt_text = None

    #What is the LED value
    value = int(intent['slots']['led']['value'])
    if(value < 0):
        value = 0
    if(value > 255):
        value = 255

    print("DEBUG set_led(): value=" + str(value) + " intent=" + intent['slots']['led']['value'])
    myResponse = requests.get(url + "/setLed?key=" + MyKey + "&set=" + str(value), verify=True)

    if(myResponse.ok):
        speech_output = "The led is set, master"        
    else:
        speech_output = "Something wrong has happened. Can't set the led"
    
    should_end_session = True
    return build_response(session_attributes, build_speechlet_response(
        intent['name'], speech_output, reprompt_text, should_end_session))


def get_temperature(intent, session):
    print("CALL: get_temperature()")
    session_attributes = {}
    reprompt_text = None

    # Which scale should be used?
    scale = "C"
    scaleLong = "Celsius"
    if((intent['slots']['scale']['value'].lower() == "fahrenheit") or (intent['slots']['scale']['value'].lower() == "f")):
        scale="F"
        scaleLong = "Fahrenheit"
    elif(intent['slots']['scale']['value'].lower() == "kelvin") or (intent['slots']['scale']['value'].lower() == "k"):
        scale="K"
        scaleLong = "Kelvin"

    print("DEBUG get_temperature(): scale=" + scale + " long scale=" + scaleLong + " intent=" + intent['slots']['scale']['value'])
    myResponse = requests.get(url + "/getT?key=" + MyKey + "&scale=" + scale, verify=True)

    if(myResponse.ok):
        jData = json.loads(myResponse.content)
        speech_output = "The temperature in your room is " + str(jData["return_value"]) + " degrees " + scaleLong

    else:
        speech_output = "Something wrong has happened. Can't get the temperature"
    
    should_end_session = True
    return build_response(session_attributes, build_speechlet_response(
        intent['name'], speech_output, reprompt_text, should_end_session))

# --------------- Events ------------------

def on_session_started(session_started_request, session):
    """ Called when the session starts """

    print("on_session_started requestId=" + session_started_request['requestId']
          + ", sessionId=" + session['sessionId'])


def on_launch(launch_request, session):
    """ Called when the user launches the skill without specifying what they
    want
    """

    print("on_launch requestId=" + launch_request['requestId'] +
          ", sessionId=" + session['sessionId'])
    # Dispatch to your skill's launch
    return get_welcome_response()


def on_intent(intent_request, session):
    """ Called when the user specifies an intent for this skill """

    print("on_intent requestId=" + intent_request['requestId'] +
          ", sessionId=" + session['sessionId'])
    print("INTENT: %s" % intent_request['intent']['name'])

    intent = intent_request['intent']
    intent_name = intent_request['intent']['name']

    # Dispatch to your skill's intent handlers
    if intent_name == "GetTemperature":
        return get_temperature(intent, session)
    elif intent_name == "SetLED":
        return set_led(intent, session)
    elif intent_name == "AMAZON.HelpIntent":
        return get_welcome_response()
    elif intent_name == "AMAZON.CancelIntent" or intent_name == "AMAZON.StopIntent":
        return handle_session_end_request()
    else:
        print("We got intent %s" % intent_name)
        raise ValueError("Invalid intent")


def on_session_ended(session_ended_request, session):
    """ Called when the user ends the session.
    Is not called when the skill returns should_end_session=true
    """
    print("on_session_ended requestId=" + session_ended_request['requestId'] +
          ", sessionId=" + session['sessionId'])
    # add cleanup logic here


# --------------- Main handler ------------------

def lambda_handler(event, context):
    """ Route the incoming request based on type (LaunchRequest, IntentRequest,
    etc.) The JSON body of the request is provided in the event parameter.
    """
    print("event.session.application.applicationId=" +
          event['session']['application']['applicationId'])

    """
    Uncomment this if statement and populate with your skill's application ID to
    prevent someone else from configuring a skill that sends requests to this
    function.
    """
    # if (event['session']['application']['applicationId'] !=
    #         "amzn1.echo-sdk-ams.app.[unique-value-here]"):
    #     raise ValueError("Invalid Application ID")

    if event['session']['new']:
        on_session_started({'requestId': event['request']['requestId']},
                           event['session'])

    if event['request']['type'] == "LaunchRequest":
        return on_launch(event['request'], event['session'])
    elif event['request']['type'] == "IntentRequest":
        return on_intent(event['request'], event['session'])
    elif event['request']['type'] == "SessionEndedRequest":
        return on_session_ended(event['request'], event['session'])