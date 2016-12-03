import sys, urllib, urllib2, json, re, logging, datetime, time

# pip install websocket-client
import websocket
# pip install pytz
import pytz

logging.basicConfig()    # ?

if len(sys.argv)!=2:
    print 'slacklogger.py token'
    exit(0)
token = sys.argv[1]

def api(method, param):
    p = {'token': token}
    p.update(param)
    req = urllib2.Request('https://slack.com/api/'+method, urllib.urlencode(p))
    res = json.loads(urllib2.urlopen(req).read())
    if not res['ok']:
        print res
        raise 'Failed'
    return res

def log(message):
    t = datetime.datetime.now(pytz.timezone('Asia/Tokyo')).strftime('%Y/%m/%d %H:%M:%S')
    print t, message
log('start')

def on_message(ws, message):
    global users
    global channels
    global wait

    message = json.loads(message)

    type = message['type']
    if type=='hello':
        wait = 1
        log('hello')
    elif type=='error':
        log('error')
        log(message['error'])
        raise 'Error'
    elif type=='channel_archive':
        log('channel_archive')
    elif type=='channel_created':
        channels[message['channel']['id']] = message['channel']['name']
        log('channel #%s created' % channels[message['channel']['id']])
    elif type=='channel_deleted ':
        log('channel #%s deleted' % channels[message['channel']])
    elif type=='channel_rename ':
        old = channels[message['channel']['id']]
        channels[message['channel']['id']] = message['channel']['name']
        log('channel #%s renamed to #%s' % (old, channels[message['channel']['id']]))
    elif type=='channel_unarchive ':
        log('channel #%s archived' % channels[message['channel']])
    elif type=='goodbye':
        log('goodbye')
    elif type=='message':
        channel = channels[message['channel']]
        user = users[message['user']]
        text = message['text']
        text = re.sub(r'<#([A-Z0-9]+)(|[^>]*)?>', lambda m: '#'+channels[m.group(1)], text) 
        text = re.sub(r'<@([A-Z0-9]+)(|[^>]*)?>', lambda m: '@'+users[m.group(1)], text) 
        text = text.replace('&amp;', '&')
        text = text.replace('&lt;', '<')
        text = text.replace('&gt;', '>')
        text = text.replace('\n', '\\n')
        if 'edited' in message:
            text += ' (edited)'
        log('#%s @%s %s' % (channel, user, text))
    elif type=='user_change':
        old = users[message['user']['id']]
        users[message['user']['id']] = message['user']['name']
        log('user @%s renamed to @%s' % (old, users[message['user']['id']]))

def on_error(ws, error):
    raise 'Error'

def on_close(ws):
    raise 'Closed'

def main():
    global users
    global channels

    res = api('rtm.start', {})

    users = {}
    for u in res['users']:
        users[u['id']] = u['name']

    channels = {}
    for c in res['channels']:
        channels[c['id']] = c['name']

    url = res['url']
    print 'URL:', url

    websocket.enableTrace(True)
    ws = websocket.WebSocketApp(
        url,
        on_message = on_message,
        on_error = on_error,
        on_close = on_close)
    ws.run_forever()

while True:
    try:
        main()
    except:
        pass
    print 'Disconnect. wait %d sec' % wait
    time.sleep(wait)
    wait = min(60, max(1, wait*2))
