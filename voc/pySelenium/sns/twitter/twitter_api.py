"""
====================================
 :mod:`twitter_ api`
====================================
.. moduleauthor:: Kyobong An <akb0930@argos-labs.com>
.. note:: ARGOS-LABS License

Description
===========
ARGOS LABS Rossum API unittest module
"""
# Authors
# ===========
#
# * Kyobong An
#
# Change Log
# --------
#
#  * [2022/10/27]
#     - article_screenshot 필드 추가
#  * [2021/06/10]
#     - title value ''로 수정
#     - 검색어가 본문에 있는지 체크로직 추가
#  * [2021/05/27]
#     - starting


import os
import sys
import yaml
import json
import tarfile
import twitter
import datetime
import traceback
import urllib.request
from copy import deepcopy
from alabs.common.util.vvlogger import get_logger


################################################################################
class Twitter_API(object):
    def __init__(self, config_f):
        if not os.path.exists(config_f):
            raise IOError(f'Cannot read config file "{config_f}"')
        with open(config_f, encoding='utf-8') as ifp:
            self.config = yaml.load(ifp, yaml.SafeLoader)
        log_d = self.config['target']['log_folder']
        if not os.path.exists(log_d):
            os.makedirs(log_d)
        self.logger = get_logger('\\'.join([log_d.replace('/', '\\'), 'NewsKmibSearch.log']),
                                 logsize=1024 * 1024 * 10)
        twitter_consumer_key = self.config['params']['site']['twitter_consumer_key']
        twitter_consumer_secret = self.config['params']['site']['twitter_consumer_secret']
        twitter_access_token = self.config['params']['site']['twitter_access_token']
        twitter_access_secret = self.config['params']['site']['twitter_access_secret']

        self.twitter_api = twitter.Api(consumer_key=twitter_consumer_key,
                                       consumer_secret=twitter_consumer_secret,
                                       access_token_key=twitter_access_token,
                                       access_token_secret=twitter_access_secret)
        # 이미지 다운(403 에러 해결코드)
        opener = urllib.request.build_opener()
        opener.addheaders = [('User-Agent',
                              'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/36.0.1941.0 Safari/537.36')]
        urllib.request.install_opener(opener)

        # for output
        start_ts = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
        folder_name = "_".join(
            [str(self.config['params']['site']['site_number']),
             self.config['params']['site']['search'],
             start_ts]
        )
        self.config['target']['folder'] += '/' + folder_name
        out_config = deepcopy(self.config)
        del out_config['params']['site']['twitter_consumer_key']
        del out_config['params']['site']['twitter_consumer_secret']
        del out_config['params']['site']['twitter_access_token']
        del out_config['params']['site']['twitter_access_secret']
        self.output = {
            'start_ts': start_ts,
            'config': out_config,
            'article_list': [],
            'latest_create_article_ts': None,
            'cafe_info': {
                'name': None,
                'url': None,
                'since': None,
                'category': None,
                'register_type': None,
                'write_condition': None,
                'num_members': None,
                'num_visitors': None,
            },
            'app_info': {
                'star_like': None,
                'num_reviews': None,
                'title': None,
                'contents': None,
                'version': None,
                'num_download': None,
            }
        }
        self.logger.info(f'Starting TWITTER Crawaling... with '
                         f'config:\n{out_config}')

    # ==========================================================================
    @staticmethod
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

    # ==========================================================================
    def get_search(self):
        articles = self.twitter_api.GetSearch(term=self.config['params']['site']['search'],
                                              count=self.config['params']['site']['max_articles'],
                                              result_type="recent",
                                              include_entities=True,
                                              return_json=True)
        return articles['statuses']

    # ==========================================================================
    def stop_article_older_than(self, msg):
        try:
            # '2021.12.21 21:48:00'
            create_ts = datetime.datetime.strptime(msg['create_ts'], '%Y.%m.%d %H:%M:%S')
            old_ts = datetime.datetime.strptime(
                self.config['params']['site']['stop_article_older_than']['datetime'],
                self.config['params']['site']['stop_article_older_than']['format']
            )
            if create_ts < old_ts:
                self.logger.error(f'Stop crawling because article create_ts "{create_ts}" '
                                  f'is older than "{old_ts}"')
                return True
            return False
        except Exception as err:
            return False

    # ==========================================================================
    def get_article(self, articles):
        for i, article in enumerate(articles):
            msg = {
                'page': None,
                'row': i + 1,
                'user_type': self.config['params']['site']['user_type'],
                'site': self.config['params']['site']['site'],
                'site_name': self.config['params']['site']['site_name'],
                # 'site_board': self.config['params']['site']['site_board'],
                'channel': self.config['params']['site']['channel'],
                'search_type': self.config['params']['site']['search_type'],
                'service': self.config['params']['site']['service'],
                'article_id': str(article['id']),
                'create_ts': (datetime.datetime.strptime(article['created_at'], '%a %b %d %H:%M:%S %z %Y') + datetime.timedelta(hours=9)).strftime('%Y.%m.%d %H:%M:%S'),
                'board_name': None,
                'title': '',
                'contents': article['text'],
                'author': article['user']['name'],
                'view_count': article['retweet_count'],
                'good': None,
                'great': None,
                'sad': None,
                'angry': None,
                'news': None,
                'like': article['favorite_count'],
                'dislike': None,
                'star_like': None,
                # retweet_count수를 리트윗수() 까지만 파악가능.
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
                'article_screenshot': None
            }
            # 검색어가 본문에 있는지 확인.
            if msg['contents'].count(self.config['params']['site']['search']) == 0:
                continue
            if self.stop_article_older_than(msg):
                continue
            if 'extended_entities' in article and 'media' in article['extended_entities']:
                for img_url in article['extended_entities']['media']:
                    msg['image_url_list'].append(img_url['media_url_https'])
            self.save_image(msg)
            self.save_article(msg)
            self.output['article_list'].append(msg)
            # 첫번째로 크롤링한 게시글의 작성시간을 저장
            if self.output["latest_create_article_ts"] is None:
                self.output["latest_create_article_ts"] = msg['create_ts']

    # ==========================================================================
    def save_image(self, article):
        # 게시글 이미지
        for j, sub_e_url in enumerate(article['image_url_list']):
            try:
                article_img_p = self.get_safe_path(
                    self.config['target']['folder'],
                    article['article_id'],
                    f'{j}.png'
                )
                # 가끔 에러 나는 경우가 있슴
                for count in range(10):
                    try:
                        urllib.request.urlretrieve(sub_e_url, article_img_p)
                        article['image_list'].append(f'{j}.png')
                        break
                    except:
                        self.logger.info(f'save_img: {j}.png : retry{count}')
                        continue
            except Exception as err:
                self.logger.error(f'save_img: {j, sub_e_url}: {str(err)}')

    # ==========================================================================
    def save_d(self, fn, d):
        fn += '.json'
        p = os.path.dirname(fn)
        if not os.path.exists(p):
            os.makedirs(p)
        with open(fn, 'w', encoding='utf-8') as ofp:
            ofp.write(json.dumps(d, ensure_ascii=False))

    # ==========================================================================
    def save_article(self, article):
        at_js_f = self.get_safe_path(
            self.config['target']['folder'],
            article['article_id'],
            article['article_id']
        )
        self.save_d(at_js_f, article)

    # ==========================================================================
    def make_tgz(self):
        src_d = self.config['target']['folder']
        tgz_f = self.config['target']['folder'] + '.tgz'
        with tarfile.open(tgz_f, "w:gz") as tar:
            tar.add(src_d, arcname=os.path.basename(src_d))

    # ==========================================================================
    def save(self):
        self.output['num_articles'] = len(self.output['article_list'])
        if self.config['target']['is_separate_article']:
            del self.output['article_list']
        js_f = self.get_safe_path(
            self.config['target']['folder'],
            f'{self.output["start_ts"]}'
        )
        self.save_d(js_f, self.output)
        if self.config['target']['is_tar_gz']:
            self.make_tgz()

    # ==========================================================================
    def start(self):
        try:
            articles = self.get_search()
            self.get_article(articles)
        except Exception as e:
            _exc_info = sys.exc_info()
            _out = traceback.format_exception(*_exc_info)
            del _exc_info
            self.logger.error(''.join(_out))
            self.logger.error(str(e))
            return 9
        finally:
            print(self.output['latest_create_article_ts'])
            print(self.config['target']['folder'])
            self.output['end_ts'] = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
            self.save()


def main(**kwargs):
    t_api = Twitter_API(kwargs['config_f'])
    t_api.start()


if __name__ == '__main__':
    main(config_f=r'twitter_api.yaml')
