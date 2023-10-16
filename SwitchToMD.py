import pymysql
import pandas as pd

## 数据库相关变量
db_user= # 用于连接数据库的用户名
db_passwd= # 用于连接数据库的用户密码
db_dbname= # 数据库中待连接的库名
db_hostname= # 数据库主机地址

## 网页相关变量
MDfile='your-link/index.md'

## font_matter
font_matter = """---
layout: docs
index: true
seo_title: switch游戏记录
---

<p>
{% image https://cdn.jsdelivr.net/gh/jylicmp/blog_static/images/icons/logos/gamming/icons8-nintendo-switch-96.png %}
{% span logo large center, switch游玩记录 %}
</p>

{% frame switchredblue | img=https://cdn.jsdelivr.net/gh/jylicmp/blog_static/images/sources/switch_id_20231014.png %}

<br>

"""

## 从数据库获取最近游玩的n个游戏，或者游玩时间最多的n个游戏
## n默认取10
def SwitchMD_GetHistoryDB(type='All', n=10):
    # 连接数据库
    conn = pymysql.connect(host=db_hostname, 
                           user=db_user, 
                           passwd=db_passwd, 
                           db=db_dbname,
                           charset='utf8')
    # 创建cursor
    cursor = conn.cursor()

    if type == 'MostPlayed':
        # 获取游玩时间最多的n个游戏
        sql = '''SELECT * from dim_switch_game_play_history
        order by totalPlayedMinutes desc
        limit 0,
        ''' + str(n) + ';'
    elif type == 'RecentPlayed':
        # 获取最近游玩的n个游戏
        sql = '''SELECT * from dim_switch_game_play_history
        order by lastPlayedAt desc
        limit 0,
        ''' + str(n) + ';'
    else:
        # 获取全部游戏
        sql = 'SELECT * from dim_switch_game_play_history ;'

    # 执行sql语句
    cursor.execute(sql)
    # 获取数据库列表信息
    col = cursor.description
    # print(col)
    # 获取全部查询信息
    re = cursor.fetchall()
    # print(re)
    # 获取的信息默认为tuple类型，将columns转换成DataFrame类型
    columns = pd.DataFrame(list(col))
    # 将数据转换成DataFrame类型，并匹配columns
    df = pd.DataFrame(list(re), columns=columns[0])
    cursor.close()
    conn.close()
    return df

def SwitchMD_QueryName(titleId):
    # 连接数据库
    conn = pymysql.connect(host=db_hostname, 
                           user=db_user, 
                           passwd=db_passwd, 
                           db=db_dbname,
                           charset='utf8')
    # 创建cursor
    cursor = conn.cursor()
    sql = '''SELECT * from dim_switch_game_name_translate_man where titleId = ''' + "'" + titleId + "' ;"
    # print(sql)
    cursor.execute(sql)
    col = cursor.description
    re = cursor.fetchall()
    columns = pd.DataFrame(list(col))
    df = pd.DataFrame(list(re), columns=columns[0])
    cursor.close()
    conn.close()
    return df

## 利用btns标签生成最近游玩游戏
def SwitchMD_PrintBtns(dict, chs=False):
    output = '<a> \n'
    name = dict['titleName']
    if chs:
        query_name = SwitchMD_QueryName(dict['titleId']).to_dict('records')
        # 判断翻译表中是否有该游戏
        if query_name==[]:
            print('=== Not exist in translate table ===')
            print('titleId: ' + dict['titleId'])
            print('titleName: ' + dict['titleName'])
            print('=== Using titleName ===')
        else:
            name = query_name[0]['CHSName']
    output = output + '<b>' + name + '</b> \n'
    output = output + '{% p center ::最后游玩日期 %} \n'
    output = output + '{% p center ::' + dict['lastPlayedAt'].strftime('%Y-%m-%d') + '%} \n'
    output = output + "<img src='" + dict['imageUrl'] + "'> \n"
    output = output + '</a> \n'
    print('done: ' + name)
    return output

## 利用wrap样式类生成最常游玩游戏
def SwitchMD_PrintWrap(dict, progress, color='blue', chs=False):
    output = '<div class="wrap"> \n'
    name = dict['titleName']
    if chs:
        query_name = SwitchMD_QueryName(dict['titleId']).to_dict('records')
        # 判断翻译表中是否有该游戏
        if query_name==[]:
            print('=== Not exist in translate table ===')
            print('titleId: ' + dict['titleId'])
            print('titleName: ' + dict['titleName'])
            print('=== Using titleName ===')
        else:
            name = query_name[0]['CHSName']
    output = output + '<img src="'+ dict['imageUrl'] + '" alt="image"> \n'
    output = output + '<div class="txt">\n<p>{% progress ' + str(progress) + ' ' + color + ' "' + str(dict['totalPlayedMinutes']//60) + '小时' + str(dict['totalPlayedMinutes']%60) + '分钟' + '"  %}</p> \n'
    output = output + '<p>' + name + '<br>游玩天数：' + str(dict['totalPlayedDays']) + '</p> \n'
    output = output + '</div> \n</div> \n'
    print('done: ' + name)
    return output

## 最常游玩游戏中，以成比例的进度条代表游玩时间，前三个游戏用红色进度条表示
def SwitchMD_PrintWrapAll(dictAll, chs=False):
    output = "<br> \n"
    i = 0
    maxtime=dictAll[0]['totalPlayedMinutes']
    for dict in dictAll:
        progress = round(dict['totalPlayedMinutes']*100 / maxtime, 2)
        if i<=2:
            color = 'red'
        else:
            color = 'blue'
        output = output + SwitchMD_PrintWrap(dict, progress, color, chs)
        output = output + '\n'
        i += 1
    return output

if __name__ == "__main__":
    print('=== Markdown file ===')
    print(MDfile)
    print('=== Routines ===')
    dict_most = SwitchMD_GetHistoryDB(type='MostPlayed', n=10).to_dict('records')
    dict_recent = SwitchMD_GetHistoryDB(type='RecentPlayed', n=10).to_dict('records')
    with open(MDfile, "w") as f:
        print("Writing: font matter")
        f.write(font_matter)
        print("========================================")

        print("Writing: most played games")
        f.write("{% span logo large, 最常游玩 %} \n<br>\n\n")
        f.write(SwitchMD_PrintWrapAll(dict_most, chs=True))
        f.write("\n<br> \n \n")
        print("========================================")

        print("Writing: recent played games")
        f.write("{% span logo large, 最近游玩 %} \n \n")
        f.write("{% btns circle center grid5 %} \n")
        for dict in dict_recent:
            f.write(SwitchMD_PrintBtns(dict, chs=True))
        f.write("{% endbtns %}")
        f.close
    print("========================================")
    print("index.md written.")
