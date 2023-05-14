import requests
import json


api_key = 'your api key'

r = requests.get(f'https://proxy6.net/api/{api_key}/getproxy')
proxies_raw = json.loads(r.text)['list']
proxies = [f"{proxies_raw[e]['host']}:{proxies_raw[e]['port']}#{proxies_raw[e]['user']}:{proxies_raw[e]['pass']}" for e in proxies_raw]
