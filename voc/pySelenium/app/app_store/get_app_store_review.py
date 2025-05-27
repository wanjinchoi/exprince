# Change Log
# --------
#  * [2024/07/23]
#     - 검색결과 없는 경우, 노출되는 페이지 변경으로 인한 모듈 수정
#  * [2024/07/17]
#     - 로그 남기도록 추가
#  * [2023/02/10]
#     - title부분에 사이트명 입력
#  * [2022/06/13]
#     - 날짜만 비교해서 해당 날짜데이터만 수집하도록 변경
#  * [2022/06/03]
#     - create_ts가 LA 시간으로 나옴. +16시간
#  * [2022/02/15]
#     - 검색기능 주석처리
#  * [2022/01/27]
#     - starting
################################################################################
import os
import sys
import yaml
import time
import json
import shutil
# import pprint
import datetime
import tarfile
import typing
import requests
import pathlib
import logging
import logging.handlers


################################################################################
# 로그 설정
def get_logger(logfile,
               logsize=500*1024, logbackup_count=4,
               logger=None, loglevel=logging.DEBUG):
    loglevel = loglevel
    pathlib.Path(logfile).parent.mkdir(parents=True, exist_ok=True)
    if logger is None:
        logger = logging.getLogger(os.path.basename(logfile))
    logger.setLevel(loglevel)
    if logger.handlers is not None and len(logger.handlers) >= 0:
        for handler in logger.handlers:
            logger.removeHandler(handler)
        logger.handlers = []
    loghandler = logging.handlers.RotatingFileHandler(
        logfile,
        maxBytes=logsize, backupCount=logbackup_count,
        encoding='utf8')
    # else:
    #     loghandler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        '%(asctime)s-%(name)s-%(levelname)s-'
        '%(filename)s:%(lineno)s-[%(process)d] %(message)s')
    loghandler.setFormatter(formatter)
    logger.addHandler(loghandler)
    return logger

################################################################################
def is_error_response(http_response, seconds_to_sleep: float = 1) -> bool:
    if http_response.status_code == 503:
        time.sleep(seconds_to_sleep)
        return False

    return http_response.status_code != 200


def get_json(url) -> typing.Union[dict, None]:
    response = requests.get(url)
    if is_error_response(response):
        return None
    json_response = response.json()
    return json_response


def get_safe_path(*_args):
    if sys.platform == 'win32':
        args = []
        for i in range(len(_args)):
            args.append(_args[i].replace('/', '\\'))
    else:
        args = _args
    p = os.path.join(*args)
    d = os.path.dirname(p)
    if not os.path.exists(d):
        os.makedirs(d)
    return p


# 리뷰별로 json형식의 파일 만드는 부분
def save_d(fn, d):
    # fn += '.yaml' if self.config['target']['is_yaml'] else '.json'
    fn += '.json'
    with open(fn, 'w', encoding='utf-8') as ofp:
        # if self.config['target']['is_yaml']:
        #     yaml.dump(d, ofp, allow_unicode=True)
        # else:
        ofp.write(json.dumps(d, ensure_ascii=False))


# 날짜 계산해서 멈추는 부분(날자만 비교하도록 변경)
def stop_article_older_than(logger, msg, stop_datetime):
    try:
        # '2021.12.21 21:48:00'
        create_ts = datetime.datetime.strptime(msg['create_ts'], '%Y.%m.%d %H:%M:%S')
        old_ts = datetime.datetime.strptime(
            stop_datetime,
            "%Y.%m.%d %H:%M:%S"
        )
        if create_ts.date() != old_ts.date():
            # logger.info(msg['article_id'] + f' Stop crawling because article create_ts "{create_ts.date()}" '
            #                   f'is older than "{old_ts.date()}"')
            return True
        return False
    except Exception as err:
        logger.error(f'stop_article_older_than: Error: "{str(err)}"')
        return False


# 리뷰별로 폴더에 저장하는 부분
def save_reviews(logger, article, target_folder):
    if len(article) == 0:
        return
    at_js_f = get_safe_path(
        target_folder,
        article['article_id'],
        article['article_id']
    )
    logger.info(article['article_id'] + ' save review')
    save_d(at_js_f, article)


# 파일 압축
def make_tgz(target_folder):
    src_d = target_folder
    tgz_f = target_folder + '.tgz'
    with tarfile.open(tgz_f, "w:gz") as tar:
        tar.add(src_d, arcname=os.path.basename(src_d))


# 리뷰 구하는 부분
def get_reviews(logger, app_id, config, page=1) -> typing.List[dict]:
    try:
        logger.info(f'Starting App Store Review Crawaling... with ' + config['params']['site']['site'] + '_' + config['params']['site']['site_name'])
        print(f'STARTED {page}')
        reviews: typing.List[dict] = [{}]

        while True:
            logger.info(f'page is  {page}')
            url = (
                f'https://itunes.apple.com/kr/rss/customerreviews/page={page}/id={app_id}/sortBy=mostRecent/json')
            u_json = get_json(url)
            if not u_json:
                return reviews
            elif 'entry' not in u_json['feed']:
                return reviews

            data_feed = u_json.get('feed')

            try:
                if not data_feed.get('entry'):
                    get_reviews(app_id, config, page + 1)

                reviews += [
                    {
                        'page': page,
                        'user_type': config['params']['site']['user_type'],
                        'site': config['params']['site']['site'],
                        'site_name': config['params']['site']['site_name'],
                        # 'site_board': config['params']['site']['site_board'],
                        'channel': config['params']['site']['channel'],
                        'search_type': config['params']['site']['search_type'],
                        'service': config['params']['site']['service'],
                        'article_id': entry.get('id').get('label'),
                        'create_ts': entry.get('updated').get('label'),
                        'board_name': None,
                        # 'title': entry.get('title').get('label'),
                        'title': config['params']['site']['site_name'],
                        'contents': entry.get('content').get('label'),
                        'author': entry.get('author').get('name').get('label'),
                        # 'author_url': entry.get('author').get('uri').get('label'),
                        'view_count': None,
                        'good': None,
                        'great': None,
                        'sad': None,
                        'angry': None,
                        'news': None,
                        'version': entry.get('im:version').get('label'),
                        'like': int(entry.get('im:voteCount').get('label')),
                        'dislike': None,
                        'star_like': int(entry.get('im:rating').get('label')),
                        'num_comments': None,
                        'article_url': None,
                        'image_list': [],
                        'image_url_list': [],
                        'attachment_name': [],
                        'attachment_url': [],
                        'comment_list': [
                            {
                                'comment_id': None,
                                'is_reply': None,
                                'parent_comment_id': None,
                                'create_ts': None,
                                'nickname': None,
                                'contents': None,
                                'like': None,
                                'dislike': None,
                                'comment_img': [],
                                'comment_img_url': [],
                            }
                        ],
                    }
                    for entry in data_feed.get('entry')
                    if not entry.get('im:name')
                ]
                page += 1
            except Exception as err:
                logger.error(f'get_review: Error: "{str(err)}"')
                return reviews
    except Exception as err:
        logger.error(f'get_reviews: Error: "{str(err)}"')
        raise


# def main(app_id, target_folder, search, stop_datetime=None):
def main(app_id, target_folder, config_f):
    with open(config_f, encoding='utf-8') as ifp:
        config = yaml.load(ifp, yaml.SafeLoader)
    log_path = config['target']['log_folder']
    if not os.path.exists(os.path.dirname(log_path)):
        os.makedirs(os.path.dirname(log_path))
    logger = get_logger(get_safe_path(log_path, 'AppStoreSearch_review.log'), logsize=1024 * 1024 * 10)
    # 멈추는 시간
    stop_datetime = config['params']['site']['stop_article_older_than']['datetime']
    reviews = get_reviews(logger, app_id=app_id, config=config)
    if not reviews[0]: del reviews[0]
    num_c = 0
    logger.info(f'All review len is {len(reviews)}')
    for review in reviews:
        review['create_ts'] = (datetime.datetime.strptime(review['create_ts'], '%Y-%m-%dT%H:%M:%S%z') + datetime.timedelta(hours=16)).strftime('%Y.%m.%d %H:%M:%S')
        if stop_article_older_than(logger, review, stop_datetime):
            continue
        save_reviews(logger, review, target_folder)
        num_c += 1
    #     if review['content'].find(search) > 0 or review['title'].find(search) > 0:
    #         save_reviews(review, target_folder)
    #         num_c += 1
    for file in os.listdir(target_folder):
         if file.endswith('.json'):
            with open(target_folder+'\\'+file, 'rb') as ifp:
                config = json.load(ifp)
                config['num_articles'] = num_c
                ifp.close()
            os.remove(target_folder+'\\'+file)
            with open(target_folder + '\\' + file, 'w', encoding='utf-8') as f:
                f.write(json.dumps(config, ensure_ascii=False))
            break

    make_tgz(target_folder)
    # print(len(reviews))
    # pprint.pprint(reviews)
