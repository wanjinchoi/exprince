import datetime
import json

from dateutil.relativedelta import relativedelta

from livecall.src import init_gservice

KST = datetime.timezone(datetime.timedelta(hours=9))


class HolidayCounter(object):
    def __init__(self, name='조성은', year=None):
        self.name = name
        self.year = year or datetime.date.today().year
        self.gservice = init_gservice()
        self.calendar_id = None
        self.init_calid()

    def init_calid(self):
        page_token = None
        calendar_id = None
        while True:
            calendar_list = self.gservice.calendarList().list(
                pageToken=page_token).execute()
            for calendar_list_entry in calendar_list['items']:
                print(calendar_list_entry['summary'])
                if calendar_list_entry['summary'] == 'VIVANS-개인일정':
                    calendar_id = calendar_list_entry['id']
                    break
            page_token = calendar_list.get('nextPageToken')
            if not page_token:
                break
        self.calendar_id = calendar_id

    def get_counter(self):
        timemin = datetime.datetime(self.year, 1, 1, 0, 0, 0, tzinfo=KST)
        timemax = timemin + relativedelta(years=1)
        r = self.gservice.events().list(
            calendarId=self.calendar_id,
            timeMin=timemin.isoformat(),
            timeMax=timemax.isoformat(),
            singleEvents=True,
            orderBy='startTime',
            timeZone='Asia/Seoul',
            maxResults=2500,
        ).execute()
        events = r.get('items', [])
        member = [
            '김태진', '박병구', '허상민', '김영준',
        ]
        r = dict((k, [0, 0, 0, []]) for k in member)

        for event in events:
            targets = []
            for k in r.keys():
                if event.get('summary') and k in event.get('summary'):
                    targets.append(k)

            if not targets:
                continue

            if event.get('start').get('date'):
                sdate = datetime.datetime.strptime(
                    event.get('start').get('date'), '%Y-%m-%d')
                edate = datetime.datetime.strptime(event.get('end').get('date'),
                                                   '%Y-%m-%d')
                tdelta = (edate - sdate).days
            else:
                tdelta = 1

            for t in targets:
                if ('반차' in event.get('summary') or
                        '오전' in event.get('summary') or
                        '오후' in event.get('summary')):
                    r[t][1] += 1
                elif '대체' in event.get('summary'):
                    r[t][2] += 1
                elif ('휴가' in event.get('summary') or
                      '휴무' in event.get('summary') or
                      '연차' in event.get('summary') or
                      '년차' in event.get('summary')):
                    r[t][0] += tdelta
                else:
                    continue
                r[t][3].append((event.get('start').get('date') or
                                event.get('start').get('dateTime'),
                                event.get('summary'),
                                tdelta))
        return r


def main():
    # hc = HolidayCounter(year=2019)
    hc = HolidayCounter()
    r = hc.get_counter()
    # sort total
    r = {k: v for k, v in sorted(r.items(),
                                 key=lambda x: x[1][0] + x[1][1]/2)}

    # sort name
    # r = {k: v for k, v in sorted(r.items(), key=lambda x: x[0])}
    for k in r:
        total = r[k][0] + r[k][1] / 2
        print('{} Total: {:4.1f}, [휴가, 반차, 대체]: {}'.format(k, total, r[k]))
    with open('holiday_results.json', 'w') as f:
        json.dump(r, f)


if __name__ == '__main__':
    main()
