import pymysql

def insert(self, vo):
    conn = pymysql.connect(host='localhost', user='viva', password='viva12@',db='example', charset='utf8')

    cur = conn.cursor()
    sql = 'insert into members values(%s,%s,%s,%s)'
    cur.execute(sql)
    vals =(vo.id, vo.pwd, vo.name, vo.email)
    cur.execute(sql, vals)
    conn.commit()
