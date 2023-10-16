import SwitchWebAPI as NSAPI
import pymysql
from sqlalchemy import create_engine,types
import pandas as pd 
import requests
import re
import urllib.parse
from datetime import datetime,timedelta

client_id = "5c38e31cd085304b"
ua = 'com.nintendo.znej/1.13.0 (Android/7.1.2)'
session_token = NSAPI.NS_GetSessionToken(client_id,ua)
access_token = NSAPI.NS_GetAccessToken(client_id, session_token)
# history = NSAPI.NS_GetPlayHistory(access_token, ua)
# print(history)

db_user= # 用于连接数据库的用户名
db_passwd= # 用于连接数据库的用户密码
db_dbname= # 数据库中待连接的库名
db_hostname= # 数据库主机地址

def SwitchDB_GamePlayHistory(history):
    titleId=[]
    titleName=[]
    deviceType=[]
    imageUrl=[]
    lastUpdatedAt=[]
    firstPlayedAt=[]
    lastPlayedAt=[]
    totalPlayedDays=[]
    totalPlayedMinutes=[]

    for i in history:
        titleId.append(i["titleId"])
        titleName.append(i["titleName"])
        deviceType.append(i["deviceType"])
        imageUrl.append(i["imageUrl"])
        lastUpdatedAt.append(i["lastUpdatedAt"])
        firstPlayedAt.append(i["firstPlayedAt"])
        lastPlayedAt.append(i["lastPlayedAt"])
        totalPlayedDays.append(i["totalPlayedDays"])
        totalPlayedMinutes.append(i["totalPlayedMinutes"])
    
    df=pd.DataFrame({"titleId":titleId,"titleName":titleName,"deviceType":deviceType,"imageUrl":imageUrl,"lastUpdatedAt":lastUpdatedAt,"firstPlayedAt":firstPlayedAt,"lastPlayedAt":lastPlayedAt,"totalPlayedDays":totalPlayedDays,"totalPlayedMinutes":totalPlayedMinutes})

    UTC9to8=lambda x: (datetime.strptime(x,"%Y-%m-%dT%H:%M:%S+09:00")-timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")

    df["lastUpdatedAt"]=df["lastUpdatedAt"].map(UTC9to8)
    df["firstPlayedAt"]=df["firstPlayedAt"].map(UTC9to8)
    df["lastPlayedAt"]=df["lastPlayedAt"].map(UTC9to8)

    # print(df)

    con_engine = create_engine('mysql+pymysql://'+db_user+':'+db_passwd+'@'+db_hostname+':3306/'+db_dbname+'?charset=utf8')

    dtype={"titleId":types.String(length=255),
            "titleName":types.String(length=255),
            "deviceType":types.String(length=255),
            "imageUrl":types.String(length=255),
            "lastUpdatedAt":types.DateTime(),
            "firstPlayedAt":types.DateTime(),
            "lastPlayedAt":types.DateTime(),
            "totalPlayedDays":types.Integer(),
            "totalPlayedMinutes":types.Integer()
    }

    df.to_sql('dim_switch_game_play_history', con_engine, dtype=dtype, if_exists='append', index = False)

def SwitchDB_QueryGame(titleId):
    # 连接数据库
    conn = pymysql.connect(host=db_hostname, 
                           user=db_user, 
                           passwd=db_passwd, 
                           db=db_dbname,
                           charset='utf8')
    # 创建cursor
    cursor = conn.cursor()
    sql = '''SELECT * from dim_switch_game_name_translate_man where titleId = ''' + "'" + titleId + "'"
    # print(sql)
    # 执行sql语句
    cursor.execute(sql)
    re = cursor.fetchall()
    # print(re)
    if re==():
        output = False
    elif re[0][0]==titleId:
        output = True
    else:
        output = False
    cursor.close()
    conn.close()
    return output

def SwitchDB_GetChineseName(titleId):
    url = 'https://tinfoil.io/Title/' + titleId
    headers = {'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36'}
    # 在第三方站点finfoil根据titleId查找游戏页面
    page = requests.get(url=url, headers=headers)
    pattern = r'url=(.+?)%2FHK"'
    matches = re.findall(pattern, page.text)
    # 判断是否包含港服跳转页面
    if matches!=[]:
        url_hk =  urllib.parse.unquote(matches[0]+'%2FHK')
        page_hk = requests.get(url=url_hk, headers=headers)
        pattern_hk = r'購買下載版軟體｜(.+?)">\n'
        matches_hk = re.findall(pattern_hk, page_hk.text)
        output = matches_hk[0]
    else:
        output = '请输入中文游戏名'
    return output

def SwitchDB_CollectName(dictAll):
    str_insert = ''
    for dict in dictAll:
        if not SwitchDB_QueryGame(dict['titleId']):
            print('Add: ' + dict['titleName'])
            tmp_cht=SwitchDB_GetChineseName(dict['titleId'])
            print('Found: ' + tmp_cht)
            str_insert = str_insert + "('" + dict['titleId'] + "','" + dict['titleName'] + "','" + tmp_cht + "'),"
        else:
            print('Skip: ' + dict['titleName'])
    str_insert = str_insert[:-1]
    # print(str_insert)

    # 连接数据库
    conn = pymysql.connect(host=db_hostname, 
                           user=db_user, 
                           passwd=db_passwd, 
                           db=db_dbname,
                           charset='utf8')
    # 创建cursor
    cursor = conn.cursor()
    sql = '''INSERT into dim_switch_game_name_translate_man (titleId, titleName, CHTName) values ''' + str_insert + ' ;'
    # print(sql)
    # 尝试写入数据库
    try:
        conn.begin()
        cursor.execute(sql)
        conn.commit()
        print('done: add to translate table')
    except Exception as e:
        conn.rollback()
        print(e)
    conn.close()


# if __name__ == "__main__":
#     SwitchDB_CollectName(history['playHistories'])
#     SwitchDB_GamePlayHistory(history['playHistories'])