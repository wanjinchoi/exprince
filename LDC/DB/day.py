from datetime import datetime
import datetime

now = datetime.datetime.now()



def main(v_date):
    year = now.year
    month = now.month
    day = 30

    first_day = datetime.date(2023, 12, 1)
    # first_day1 = datetime.date(year, month, 30)
    first_day_weekday = first_day.weekday()
    # first_day_weekday1 = first_day1.weekday()
    week_number = (day + ((first_day_weekday + 1) % 7) - 1) // 7 + 1
    week = str(week_number)


    return week



if __name__ == "__main__":
    main('aa')