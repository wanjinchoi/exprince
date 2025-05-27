import re
import json
import operator
import sys

# 테스트 실행 코드
# python -m argoslabs.etc.run_python_script argoslabs/etc/run_python_script/tests/test_2.py -a 51sig1lT7YNWXgOmfUOqw8EMs_bFEj5995eFtiXBt3VLVPj3gSl7IJkG-k5XUFXIjo_Oibk1gGYSJSY99iCMD02e6IXaa3k_zFdgbXgdHXMPc4kxzICtKEFjv63h-dn2eRtSiw_G2G4lfKZX-aBizEs_uFf5kO0dOTJ_xRC34EyngTuOEzy2QTWyfApNe6GiD-CGSFX6pbSDtwmLj9-C_F18iAk6L5Zae1VzieGYUS3qBE6NzY12QX9j14j0MfQqTAhKVOXCb0Fi5vPGzWRFt2_WV29ouaQa5gjT60JStTM= -a 37.5088318832 -a 127.034317309
def main(*args):
    if sys.platform == 'win32':
        plugin = 'argoslabs.api.requests.exe'
    else:
        plugin = 'argoslabs.api.requests'

    next_token = ''
    retv = list()

    header = [
        'name', #가게명
        'address',  # 주소
        'reviewRating',  # 평점
        'reviewCount',  # 리뷰수
        'estimatedDeliveryTime',  # 배달예상시간
        'deliveryFeeInfo',  # 배달비
        'serviceFeeInfo',
        'newStoreBadge',  # 신규아이콘(y / n)
    ]
    retv.append(', '.join(header))

    while True:
        cmd = [
            f'{plugin} GET ',
            'https://api.coupangeats.com/endpoint/store.get_clp',
            # '--params "categoryId:2"',
            '--params "nextToken:{}"'.format(next_token),
            '--params "badgeFilters:"',
            '--headers "X-EATS-OS-TYPE: ANDROID"',
            '--headers "X-EATS-ACCESS-TOKEN: {}"'.format(args[0]),
            '--headers "X-EATS-DEVICE-DENSITY: XXHDPI"',
            '--headers "X-EATS-DEVICE-ID: 4af74da3-4f85-32fa-80dd-1b1aba0aa592"',
            '--headers "X-EATS-NETWORK-TYPE: wifi"',
            '--headers "User-Agent: Android-Coupang-Eats-Customer/1.1.34"',
            '--headers "X-EATS-TIME-ZONE: Asia/Seoul"',
            '--headers "X-EATS-DEVICE-MODEL: SM-G960N"',
            '--headers "X-EATS-APP-VERSION: 1.1.34"',
            '--headers "X-EATS-LOCALE: ko-KR"',
            '--headers "X-EATS-SESSION-ID: d808d2c2-73ff-4326-bd7a-cfe4d4b06cd0"',
            '--headers "X-EATS-RESOLUTION-TYPE: 1080x2076"',
            '--headers "X-EATS-OS-VERSION: 8.0.0"',
            '--headers "X-EATS-PCID: 4af74da3-4f85-32fa-80dd-1b1aba0aa592"',
            '--headers "Accept-Language: ko-KR"',
            '--headers "X-EATS-LOCATION: {{\\"addressId\\":4404538,\\"latitude\\":{0},\\"longitude\\":{1},\\"zipcode\\":\\"06108\\"}}" '.format(args[1], args[2]),
            # '--headers "X-EATS-LOCATION: {\"addressId\":4404538,\"latitude\":{37.5088318832,\"longitude\":127.034317309,\"zipcode\":\"06108\"}"',
            '--headers "Host: api.coupangeats.com" --headers "Connection: Keep-Alive" --headers "Accept-Encoding: gzip"',
        ]
        cmd = ' '.join(cmd)

        out = run_plugin(cmd)
        data = json.loads(out)

        for entity in data['data']['entityList']:
            # print(entity['entity'])
            if 'storeCardWithMenu' != entity['viewType']:
                continue
            value = operator.itemgetter(*header)(entity['entity']['data'])
            value = list(value)

            # value[5] = re.findall(r'.*', value[5])[0]
            value[6] = re.findall(r'배달비 (.*)', value[6][0]['text'])[0]
            value[7] = 'y' if value[7] else 'n'

            v = ', '.join(map(lambda v: str(v).replace(',', ''), value))
            retv.append(v)

        next_token = data['data']['nextToken']
        if not next_token:
            break

    out = '\n'.join(retv)
    return out
