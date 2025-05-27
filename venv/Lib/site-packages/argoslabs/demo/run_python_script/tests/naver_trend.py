import sys
import json
import subprocess
import operator
import logging
from urllib import parse

logger = logging.getLogger('naver-trend')
# 테스트 실행 코드


def get_query_group(tags:list):
    """
    tags: ['현대, 현대 자동차, 현대 건설 ', '삼성, 삼성 바이오, 삼성 전자']
    return: '현대__SZLIG__현대,현대+자동차,현대+건설__OUML__삼성__SZLIG__삼성+바이오,삼성+전자'
    """
    tags = map(str.strip, tags)
    tags = [x.replace(' ', '+') for x in tags]
    tags = map(parse.quote, tags)
    tags = [x.split(',') for x in tags]
    keyword = list()
    for t in tags:
        keyword.append(f'{t[0].replace("+", " ")}__SZLIG__{",".join(t)}')

    result = '__OUML__'.join(keyword)
    return result


def main(*args):
    keyword = get_query_group(args)
    cmd = "curl 'https://datalab.naver.com/qcHash.naver'" \
          " -H 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:83.0) Gecko/20100101 Firefox/83.0' " \
          "-H 'Accept: */*' " \
          "-H 'Accept-Language: ko-KR,ko;q=0.8,en-US;q=0.5,en;q=0.3' --compressed " \
          "-H 'Referer: https://datalab.naver.com/' " \
          "-H 'Content-Type: application/x-www-form-urlencoded; charset=UTF-8' " \
          "-H 'X-Requested-With: XMLHttpRequest' " \
          "-H 'Origin: https://datalab.naver.com' " \
          "-H 'Connection: keep-alive' " \
          "-H 'Cookie: NRTK=ag#all_gr#1_ma#-2_si#0_en#0_sp#0; BMR=s=1610137959459&r=https%3A%2F%2Fm.blog.naver.com%2Fdreamkonkuk%2F222101938481&r2=https%3A%2F%2Fwww.google.com%2F; _datalab_cid=50000006' " \
          "-H 'TE: Trailers' " \
          f"--data-raw 'queryGroups={keyword}&startDate=20200112&endDate=20210112&timeUnit=date&gender=&age=&device='"

    with subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE) as proc:
        import time
        time.sleep(5)
        result = proc.stdout.read()
        data = json.loads(result.decode('utf-8'))
        print(data)

    cmd = f'wget -O /tmp/trend.xls https://datalab.naver.com/qcExcel.naver?hashKey={data["hashKey"]}'
    c = subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE)
    exit_code = c.wait()
    if exit_code != 0:
        logger.error('wget error')
        return ''

    return f'/tmp/trend.xls'



