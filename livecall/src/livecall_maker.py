import calendar
import datetime
from dataclasses import dataclass

import pymysql
from dateutil.relativedelta import relativedelta

from livecall.src import init_gservice

#[2024-06-19] live call 멤버 교체
# 허상민 -> 최현호  / 김태진1 -> 김주원 / 시간도 09:00~ 19:00시로 바꿈
#   None,  # saturday 있는 아랫 부분으로 일요일 야간 멤버 고정할수있음
#   162라인에 if last_memeber=='허상민'넣은 이유는 허상민->최현호 바뀌었는데 적용이 안되서 바꿈
#


# Todo: 멤버를 Json 파일로 입력 받도록
member = {
    "workday_daytime": [(
        "김주원",
        "김주원",
        "김주원",
        "김주원",
        "김주원",
    ), (
        "강민호",
        "강민호",
        "강민호",
        "강민호",
        "강민호",

    )],
    "workday_daytime_sub": (
            "김영준1",
    ),
    "workday_night": {
        "active": (
            "김주원1",
            "박병구",
            "강민호",
            "김영준1",
            "김태진",
            None,  # saturday
            "김영준2",
        ),
        "standby": (
            "박병구",
            "강민호",
            "김영준1",
            "김태진",
            "김영준2",
            None,  # saturday

            "김주원1",
        )
    },
    "holiday":(
        "김주원1",
        "김영준1",
        "박병구",
        "김태진",
        "강민호",
        "김영준2",
    )
    # holiday 는 2022년 11월 기준으로 순서 바꿈, 매년 11월 역순으로 변경해야 함.
}
SCOPES = ['https://www.googleapis.com/auth/calendar']
KST = datetime.timezone(datetime.timedelta(hours=9))


@dataclass
class AlarmNotiManager:
    dutydate: datetime
    daynight: str
    mainsub: int
    manager_name: str
    dutyenddate: datetime
    etc: str
    type: str


class LivecallMaker(object):
    def __init__(self, conn=None, rebuild=None, year=None, month=None):
        self.conn = conn
        self.rebuild = rebuild
        today = datetime.date.today()
        self.year = year or (today + relativedelta(months=1)).year
        self.month = month or (today + relativedelta(months=1)).month
        _, self.lastday = calendar.monthrange(self.year, self.month)
        self.holiday_list = []
        self.get_holiday()
        self.idx_holiday_act = None
        self.idx_holiday_stb = None
        self.db_member_list = []
        self.cal_list = []
        self.weeks = list(calendar.day_abbr)
        self.gservice = init_gservice()
        self.calendar_id = None
        self.init_calid()

    def workday_daytime(self):
        for day in range(1, self.lastday + 1):
            now = datetime.date(self.year, self.month, day)
            weekyear = now.isocalendar()[1]
            duty_active = 0
            # weekyear % 2
            duty_standby = 1
            # (weekyear + 1) % 2
            weekday = now.weekday()
            if self.is_workday(weekday) and now not in self.holiday_list:
                dutydate = f'{now} 09:00:00'
                dutyenddate = f'{now} 19:00:00'

                aman = member.get('workday_daytime')[duty_active][weekday]
                # aman2 = member.get('workday_daytime')[duty_active + 1][weekday]
                self.db_member_list.append(
                    AlarmNotiManager(dutydate, 'D', 1, aman, dutyenddate,
                                     'newtype', ''))

                sman = member.get('workday_daytime')[duty_standby][weekday]
                self.db_member_list.append(
                    AlarmNotiManager(dutydate, 'D', 1, sman, dutyenddate,
                                     'newtype', ''))

                for man in member.get('workday_daytime_sub'):
                    self.db_member_list.append(
                        AlarmNotiManager(dutydate, 'D', 3, man, dutyenddate,
                                         'newtype', ''))

                print(now, 'D', aman, sman)

    def workday_night(self):
        for day in range(1, self.lastday + 1):
            now = datetime.date(self.year, self.month, day)
            weekday = now.weekday()
            if not self.is_saturday(weekday):
                dutydate = f'{now} 19:00:00'
                dutyenddate = f'{now + relativedelta(days=1)} 09:00:00'

                aman = member.get('workday_night').get('active')[weekday]
                self.db_member_list.append(
                    AlarmNotiManager(dutydate, 'N', 1, aman, dutyenddate,
                                     'newtype', 'dutyrota'))

                sman = member.get('workday_night').get('standby')[weekday]
                self.db_member_list.append(
                    AlarmNotiManager(dutydate, 'N', 2, sman, dutyenddate,
                                     'newtype', 'dutyrota'))

                cal = dict()
                cal['date'] = f'{now}'
                cal['summary'] = f'2.야간:{aman},{sman}'
                self.cal_list.append(cal)
                print(now, 'N', aman, sman)

    def weekend_and_holiday(self):
        with self.conn.cursor() as cursor:
            sql = """
SELECT manager_name
FROM alarm_noti_manager
WHERE dutydate < %s
    AND TYPE = 'duty'
    AND mainsub = 2
ORDER BY dutydate DESC
LIMIT 1
            """
            cursor.execute(sql, f'{self.year}-{self.month}-01')
            row = cursor.fetchone()
            last_member = row.get('manager_name')
            if last_member =='허상민':
                last_member = '최현호'
        try:
            self.idx_holiday_act = member.get('holiday').index(last_member)
        except ValueError:
            self.idx_holiday_act = 0
        self.idx_holiday_stb = self.idx_holiday_act + 1

        for day in range(1, self.lastday + 1):
            now = datetime.date(self.year, self.month, day)
            weekday = now.weekday()
            if weekday in (5, 6) or now in self.holiday_list:
                if self.is_saturday(weekday):
                    self.make_holiday(now, 'D', weekday)
                    self.make_holiday(now, 'N', weekday)
                else:
                    self.make_holiday(now, 'D', weekday)

    def make_holiday(self, now, daynight, weekday):
        dutydate = None
        dutyenddate = None
        if daynight == 'D':
            dutydate = f'{now} 09:00:00'
            if self.is_saturday(weekday):
                dutyenddate = f'{now} 21:00:00'
            else:
                dutyenddate = f'{now} 19:00:00'
        elif daynight == 'N':
            dutydate = f'{now} 21:00:00'
            dutyenddate = f'{now + relativedelta(days=1)} 09:00:00'

        aman, self.idx_holiday_act = self.get_holiday_man(self.idx_holiday_act)
        self.db_member_list.append(
            AlarmNotiManager(dutydate, daynight, 1, aman, dutyenddate,
                             'newtype', 'duty'))

        sman, self.idx_holiday_stb = self.get_holiday_man(self.idx_holiday_stb)
        self.db_member_list.append(
            AlarmNotiManager(dutydate, daynight, 2, sman, dutyenddate,
                             'newtype', 'duty'))
        print(now, daynight, aman, sman)

        self.idx_holiday_act += 1
        self.idx_holiday_stb += 1

        cal = dict()
        cal['date'] = f'{now}'
        if daynight == 'D':
            cal['summary'] = f'1.주간:{aman},{sman}'
        else:
            cal['summary'] = f'2.야간:{aman},{sman}'
        self.cal_list.append(cal)

    @staticmethod
    def get_holiday_man(idx):
        try:
            return member.get('holiday')[idx], idx
        except IndexError:
            idx = 0
            return member.get('holiday')[idx], idx

    def get_holiday(self):
        with self.conn.cursor() as cursor:
            sql = """
SELECT dutydate
FROM alarm_noti_plusday
WHERE dutydate >= %s
            """
            dutydate = datetime.date(self.year, self.month, 1)
            cursor.execute(sql, dutydate)
            rows = cursor.fetchall()
            for r in rows:
                self.holiday_list.append(r.get('dutydate').date())

    def insert_db(self):
        values_list = []
        for m in self.db_member_list:
            values = []
            for k in m.__dataclass_fields__.keys():
                values.append(f"'{m.__getattribute__(k)}'")
            values.append(f"DAYOFWEEK('{m.dutydate}')")
            values_list.append(f"({','.join(values)})")

        with self.conn.cursor() as cursor:
            from_date = f'{self.year}-{self.month}-01'
            to_date = f'{self.year}-{self.month}-{self.lastday}'
            sql = f"""
DELETE FROM alarm_noti_manager
WHERE DATE(dutydate) >= '{from_date}' and DATE(dutydate) <= '{to_date}'
            """
            cursor.execute(sql)

            sql = f"""
INSERT INTO alarm_noti_manager (dutydate, daynight, mainsub, manager_name
    , dutyenddate, etc, type, week) 
VALUES {','.join(values_list)}
            """
            cursor.execute(sql)
        self.conn.commit()

    def insert_gcalendar(self):
        timemin = datetime.datetime(self.year, self.month, 1, 0, 0, 0,
                                    tzinfo=KST)
        timemax = timemin + relativedelta(months=1)
        r = self.gservice.events().list(
            calendarId=self.calendar_id,
            timeMin=timemin.isoformat(),
            timeMax=timemax.isoformat(),
            singleEvents=True
        ).execute()
        events = r.get('items', [])
        if not events:
            print("No events to delete")
        for event in events:
            print('del', event.get('start').get('date'), event.get('summary'))
            self.gservice.events().delete(
                calendarId=self.calendar_id,
                eventId=event.get('id'),
            ).execute()

        for c in self.cal_list:
            print(c)
            event = {
                'summary': f"{c.get('summary')}",
                'start': {
                    'date': f"{c.get('date')}",
                },
                'end': {
                    'date': f"{c.get('date')}",
                },
                'transparency': 'transparent',
            }
            r = self.gservice.events().insert(
                calendarId=self.calendar_id,
                body=event,
            ).execute()
            print(r.get('status'), r.get('htmllink'))

    def is_workday(self, weekday):
        if self.weeks.index('Mon') <= weekday <= self.weeks.index('Fri'):
            return True
        else:
            return False

    def is_saturday(self, weekday):
        if self.weeks.index('Sat') == weekday:
            return True
        else:
            return False

    def init_calid(self):
        page_token = None
        calendar_id = None
        while True:
            calendar_list = self.gservice.calendarList().list(
                pageToken=page_token).execute()
            for calendar_list_entry in calendar_list['items']:
                print(calendar_list_entry['summary'])
                if calendar_list_entry['summary'] == 'VIVANS-LiveCall':
                    calendar_id = calendar_list_entry['id']
                    break
            page_token = calendar_list.get('nextPageToken')
            if not page_token:
                break
        self.calendar_id = calendar_id


def main():
    # Todo: db info 환경변수로
    conn = pymysql.connect(host='argos1dbm.vivans.net',
                           port=13306,
                           user='argosdev',
                           password='$%^argos!@#',
                           db='argos_db',
                           cursorclass=pymysql.cursors.DictCursor)

    try:
        maker = LivecallMaker(conn=conn,
                              month=6,
                              year=2025,
                              rebuild=True, )
        maker.workday_daytime()
        maker.workday_night()
        maker.weekend_and_holiday()
        # Todo: delete 와 분리
        maker.insert_db()
        maker.insert_gcalendar()
    finally:
        conn.close()


if __name__ == '__main__':
    # Todo: 사용법 문서로 정리
    # Todo: 도커 빌드
    # Todo: requirements setup 파일
    # Todo: Parameter 로 year month 입력 받게
    main()
