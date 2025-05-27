import requests
import json

url = 'https://openapi.zalo.me/v3.0/oa/group/creategroupwithoa'
headers = {
    'access_token': 'iXTL1kCRxo2z7Lm0vH7bBBiVLmlc3vicwmTRLleBcGhyJNGhm02tMz5LVXNx1ALmrsDYLF1khWR8PH1zsZgjNu9dIIgj2lLpls8tKEKAYol_MZXSpr3o1-meEYJjGE92nXa07-L5isNZ3NL0qconOFL_T1hm8hnbzaPm4jevoqpKJorlw23oDUbAI7ksG_Crl311G8SsY3o1JqPCfIAOA9LbUskV8xmebLa1Qwm3l1kFRtr7WHl14PDg0MQu9CK_b2iYHOqYd1cNQrq-Y2tkVBX0KGceH-ymhGmyVOu4Wo--Os1MlJkb5RytL7MTRQyahMLmMAuYjoMVS712bGEMPvjyV3AU2ASLXWOODg1HuXEF7ojmWa2IChmF8HMzMDfAv5SpChmCZLJv1qq3qa2tS_4Q3XHNI6W-YnJk1-yd'
}
params = {
    'data': '{"offset":0,"count":15,"last_interaction_period":"TODAY","is_follower":"true"}'
}

# GET 요청
response = requests.get(url, headers=headers, params=params)

# 응답을 JSON 형식으로 출력
print(response.json())