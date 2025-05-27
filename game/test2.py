H = range(0,24)
M = range(0,60)

from datetime import datetime
from dateutil.relativedelta import relativedelta

sangyoung = input("알람시간:")
b = datetime.strptime(sangyoung,'%H%M')
c = b - relativedelta(minutes=45)
d = c.strftime('%H %M')
print(d)
