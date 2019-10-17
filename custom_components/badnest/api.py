from datetime import time, timedelta, datetime
import json

import requests

API_URL = 'https://home.nest.com'

class NestAPI():

    USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36"
    URL_JWT = "https://nestauthproxyservice-pa.googleapis.com/v1/issue_jwt"

    def __init__(self, conf_type, email, password, issue_token, cookie, api_key):
        self._user_id = None
        self._access_token = None
        self._device_id = None
        self._shared_id = None
        self._czfe_url = None
        self._compressor_lockout_enabled = None
        self._compressor_lockout_time = None
        self._hvac_ac_state = None
        self._hvac_heater_state = None
        self.mode = None
        self._time_to_target = None
        self._fan_timer_timeout = None
        self.can_heat = None
        self.can_cool = None
        self.has_fan = None
        self.fan = None
        self.away = None
        self.current_temperature = None
        self.target_temperature = None
        self.target_temperature_high = None
        self.target_temperature_low = None
        self.current_humidity = None

        if conf_type == 'nest':
            self._login_nest(email, password)
        elif conf_type == 'google':
            self._login_google(issue_token, cookie, api_key)
        self.update()

    def _login_nest(self, email, password):
        r = requests.post(f'{API_URL}/session', json={
            'email': email,
            'password': password
        })
        self._user_id = r.json()['userid']
        self._access_token = r.json()['access_token']

    def _login_google(self, issue_token, cookie, api_key):
        headers = {
            'Sec-Fetch-Mode': 'cors',
            'User-Agent': self.USER_AGENT,
            'X-Requested-With': 'XmlHttpRequest',
            'Referer': 'https://accounts.google.com/o/oauth2/iframe',
            'cookie': cookie
        }
        r = requests.get(url = issue_token, headers = headers) 
        access_token = r.json()['access_token']

        headers = {
            'Authorization': 'Bearer ' + access_token,
            'User-Agent': self.USER_AGENT,
            'x-goog-api-key': api_key,
            'Referer': 'https://home.nest.com'
        }
        params = {
            "embed_google_oauth_access_token": True,
            "expire_after": '3600s',
            "google_oauth_access_token": access_token,
            "policy_id": 'authproxy-oauth-policy'
        }
        r = requests.post(url=self.URL_JWT, headers = headers, params=params)
        jwt_token = r.json()['jwt']
        self._user_id = r.json()['claims']['subject']['nestId']['id']
        self._access_token = r.json()['jwt']

    def get_action(self):
        if self._hvac_ac_state:
            return 'cooling'
        elif self._hvac_heater_state:
            return 'heating'
        else:
            return 'off'

    def update(self):
        r = requests.post(f'{API_URL}/api/0.1/user/{self._user_id}/app_launch', json={
            "known_bucket_types": ['shared', 'device'],
            "known_bucket_versions": []
        },
        headers={
            "Authorization": f'Basic {self._access_token}'
        })
        
        self._czfe_url = r.json()['service_urls']['urls']['czfe_url']
        
        for bucket in r.json()['updated_buckets']:
            if bucket['object_key'].startswith('shared.'):
                self._shared_id = bucket['object_key']
                thermostat_data = bucket['value']
                self.current_temperature = thermostat_data['current_temperature']
                self.target_temperature = thermostat_data['target_temperature']
                self._compressor_lockout_enabled = thermostat_data['compressor_lockout_enabled']
                self._compressor_lockout_time = thermostat_data['compressor_lockout_timeout']
                self._hvac_ac_state = thermostat_data['hvac_ac_state']
                self._hvac_heater_state = thermostat_data['hvac_heater_state']
                self.mode = thermostat_data['target_temperature_type']
                self.target_temperature_high = thermostat_data['target_temperature_high']
                self.target_temperature_low = thermostat_data['target_temperature_low']
                self.can_heat = thermostat_data['can_heat']
                self.can_cool = thermostat_data['can_cool']
            elif bucket['object_key'].startswith('device.'):
                self._device_id = bucket['object_key']
                thermostat_data = bucket['value']
                self._time_to_target = thermostat_data['time_to_target']
                self._fan_timer_timeout = thermostat_data['fan_timer_timeout']
                self.has_fan = thermostat_data['has_fan']
                self.fan = thermostat_data['fan_timer_timeout'] > 0
                self.current_humidity = thermostat_data['current_humidity']
                self.away = thermostat_data['home_away_input']

    def set_temp(self, temp, temp_high = None):
        if temp_high is None:
            requests.post(f'{self._czfe_url}/v5/put', json={
                'objects': [{
                    'object_key': self._shared_id,
                    'op': 'MERGE',
                    'value':{
                        'target_temperature': temp
                    }
                }]
            },
            headers={
                'Authorization': f'Basic {self._access_token}'
            })
        else:
            requests.post(f'{self._czfe_url}/v5/put', json={
                'objects': [{
                    'object_key': self._shared_id,
                    'op': 'MERGE',
                    'value': {
                        'target_temperature_low': temp,
                        'target_temperature_high': temp_high
                    }
                }]
            },
            headers={
                'Authorization': f'Basic {self._access_token}'
            })
            

    def set_mode(self, mode):
        requests.post(f'{self._czfe_url}/v5/put', json={
            'objects': [{
                'object_key': self._shared_id,
                'op': 'MERGE',
                'value':{
                    'target_temperature_type': mode
                }
            }]
        },
        headers={
            'Authorization': f'Basic {self._access_token}'
        })

    def set_fan(self, date):
        requests.post(f'{self._czfe_url}/v5/put', json={
            'objects': [{
                'object_key': self._device_id,
                'op': 'MERGE',
                'value':{
                    'fan_timer_timeout': date
                }
            }]
        },
        headers={
            'Authorization': f'Basic {self._access_token}'
        })

    def set_eco_mode(self):
        requests.post(f'{self._czfe_url}/v5/put', json={
            'objects': [{
                'object_key': self._device_id,
                'op': 'MERGE',
                'value':{
                    'eco': {
                        'mode': 'manual-eco'
                    }
                }
            }]
        },
        headers={
            'Authorization': f'Basic {self._access_token}'
        })