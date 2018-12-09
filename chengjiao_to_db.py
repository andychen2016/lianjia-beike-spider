#!/usr/bin/env python
# coding=utf-8
# author: andychen
# 此代码仅供学习与交流，请勿用于商业用途。
# read data from csv, write to database
# database includes: mysql/mongodb/excel/json/csv

import os
from lib.utility.path import DATA_PATH
from lib.zone.city import *
from lib.item.chengjiao import *
from lib.utility.date import *
from lib.utility.version import PYTHON_3
from lib.spider.base_spider import SPIDER_NAME



if __name__ == '__main__':
    # 设置目标数据库
    ##################################
    # database = "mongodb"
    # database = "excel"
    # database = "json"
    database = "csv"
    ##################################
    db = None
    collection = None
    workbook = None
    csv_file = None
    datas = list()

    if database == "mongodb":
        from pymongo import MongoClient
        conn = MongoClient('localhost', 27017)
        db = conn.lianjia  # 连接lianjia数据库，没有则自动创建
        collection = db.chengjiao  # 使用xiaoqu集合，没有则自动创建
    elif database == "excel":
        import xlsxwriter
        workbook = xlsxwriter.Workbook('chengjiao.xlsx')
        worksheet = workbook.add_worksheet()
    elif database == "json":
        import json
    elif database == "csv":
        csv_file = open("chengjiao.csv", "w")
        line = "城市," + CSV_HEADER
        csv_file.write(line)

    city = get_city()
    # 准备日期信息，爬到的数据存放到日期相关文件夹下
    date = get_date_string()
    # 获得 csv 文件路径
    # date = "20180331"   # 指定采集数据的日期
    # city = "sh"         # 指定采集数据的城市
    city_ch = get_chinese_city(city)
    csv_dir = "{0}/{1}/chengjiao/{2}/{3}".format(DATA_PATH, SPIDER_NAME, city, date)

    files = list()
    if not os.path.exists(csv_dir):
        print("{0} does not exist.".format(csv_dir))
        print("Please run 'python chengjiao.py' firstly.")
        print("Bye.")
        exit(0)
    else:
        print('OK, start to process ' + get_chinese_city(city))
    for csv in os.listdir(csv_dir):
        data_csv = csv_dir + "/" + csv
        # print(data_csv)
        files.append(data_csv)

    # 清理数据
    count = 0
    row = 0
    col = 0
    for csv in files:
        with open(csv, 'r') as f:
            for line in f:
                count += 1
                text = line.strip()
                try:
                    # 如果小区名里面没有逗号，那么总共是6项
                    if text.count(',') == 9:
                        date, district, area, xiaoqu, initial_total_price, comunity_average_price, final_total_price, average_price, desc, raise_or_fall = text.split(',')
                    elif text.count(',') < 9:
                        continue
                    else:
                        fields = text.split(',')
                        date = fields[0]
                        district = fields[1]
                        area = fields[2]
                        xiaoqu = ','.join(fields[3:-2])
                        price = fields[-2]
                        raise_or_fall = fields[-1]
                except Exception as e:
                    print(text)
                    print(e)
                    continue
                
                print("{0} {1} {2} {3} {4} {5}".format(date, district, area, xiaoqu, average_price, raise_or_fall))
               
                # 写入mongodb数据库
                if database == "mongodb":
                    data = dict(city=city_ch, date=date, district=district, area=area, xiaoqu=xiaoqu, price=average_price,
                                raise_or_fall=raise_or_fall)
                    collection.insert(data)
                elif database == "excel":
                    if not PYTHON_3:
                        worksheet.write_string(row, col, unicode(city_ch, 'utf-8'))
                        worksheet.write_string(row, col + 1, date)
                        worksheet.write_string(row, col + 2, unicode(district, 'utf-8'))
                        worksheet.write_string(row, col + 3, unicode(area, 'utf-8'))
                        worksheet.write_string(row, col + 4, unicode(xiaoqu, 'utf-8'))
                        worksheet.write_number(row, col + 5, price)
                        # worksheet.write_number(row, col + 6, sale)
                    else:
                        worksheet.write_string(row, col, city_ch)
                        worksheet.write_string(row, col + 1, date)
                        worksheet.write_string(row, col + 2, district)
                        worksheet.write_string(row, col + 3, area)
                        worksheet.write_string(row, col + 4, xiaoqu)
                        worksheet.write_number(row, col + 5, price)
                        # worksheet.write_number(row, col + 6, sale)
                    row += 1
                elif database == "json":
                    data = dict(city=city_ch, date=date, district=district, area=area, xiaoqu=xiaoqu, price=price,
                                raise_or_fall=raise_or_fall)
                    datas.append(data)
                elif database == "csv":
                    line = "{0},{1},{2},{3},{4},{5},{6},{7},{8},{9},{10}\n".format(city_ch, date, district, area, xiaoqu, initial_total_price, comunity_average_price, final_total_price, average_price, desc, raise_or_fall)
                    csv_file.write(line)

    # 写入，并且关闭句柄
    if database == "excel":
        workbook.close()
    elif database == "json":
        json.dump(datas, open('xiaoqu.json', 'w'), ensure_ascii=False, indent=2)
    elif database == "csv":
        csv_file.close()

    print("Total write {0} items to database.".format(count))
