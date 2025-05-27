import requests
import json

url = 'https://openapi.zalo.me/v3.0/oa/group/creategroupwithoa'
headers = {
    'access_token': 'E57gCd_7E5KtM-CqUSqoMJ5Pw3zwqtq8V2EfQ4RAE5ngEfGnUUicFMmXaL5LzXuqMHVDM4NZM5Tw4lP5HzjDO5vFdLDIkJrCTYdeHbZ2UoLo4yqsFFb707K_xcTO-7vVS2ggSqRh71Ho7iq2H_TvCmbXqbuIz6j6DIJTM1_jMrGp7FHq8zmdJpPEW5igWJbW9c_f36pcOJGXARjN3_KFCYiRsI5aY6azTbpEANcmMabYPVzEIAXkQnjxn0uShbOl4aBn45ZH8X9i1eyWSz4LFqmYi2zGvmCBVnhP6tFGK3rhDVG4V-XjP7a4pMbsaqnpFssMPtBuHrfz5krrDS9B4N8soWCutN05F4767Gp842iA8OSS9-DL5cqlyG5aurKVAYB3VYB4U7aO5TOUDeXTSXXqZ5Kvf2PjVgJZLNBRE58',
    'Content-Type': 'application/json'
}
data = {
    "group_name": "ARGOS2",
    "group_description": "Argos_group2",
    "asset_id": "9a6c9dbb54e6bdb8e4f7",
    "member_user_ids": [
        "624888356634678177"
    ]
}

# JSON 데이터로 변환하여 POST 요청
response = requests.post(url, headers=headers, data=json.dumps(data))

# 응답을 JSON 형식으로 출력
print(response.json())