import os, requests, websocket, time, datetime, json, re

if 'SLACK_TOKEN' not in os.environ:
    print('SLACK_TOKEN=... python -u slacklogger.py')
token = os.environ['SLACK_TOKEN']

def api(method, param):
    p = {'token': token}
    p.update(param)
    res = requests.post('https://slack.com/api/'+method, p).json()
    if not res['ok']:
        print(res)
        raise 'Failed'
    return res

def log(message):
    t = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).strftime('%Y/%m/%d %H:%M:%S')
    print(t, message)
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
        log('channel #%s archived' % channels[message['channel']])
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
        channel = channels[message['channel']] if 'channel' in message else ''
        user = users[message['user']] if 'user' in message else ''
        text = message['text'] if 'text' in message else ''
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
    for c in res['groups']:
        channels[c['id']] = c['name']

    url = res['url']
    print('URL:', url)

    ws = websocket.WebSocketApp(
        url,
        on_message = on_message,
        on_error = on_error,
        on_close = on_close)
    ws.run_forever()

wait = 1
while True:
    try:
        main()
    except:
        pass
    print('Disconnect. wait %d sec' % wait)
    time.sleep(wait)
    wait = min(60, max(1, wait*2))
