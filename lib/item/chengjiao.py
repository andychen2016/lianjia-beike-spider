#!/usr/bin/env python
# coding=utf-8
# author: zengyuetian
# 二手房成交的数据结构

CSV_HEADER = "日期,区县,板块,小区,挂牌总价,小区平均单价,成交价,成交单价,房子简介,涨跌幅\n"

class ChengJiao(object):
    def __init__(self, district, area, name, initial_total_price, final_total_price, average_price, comunity_average_price, desc):
        self.district = district
        self.area = area
        self.name = name
        self.initial_total_price = initial_total_price
        self.comunity_average_price = comunity_average_price.replace("元/平", "")
        self.final_total_price = final_total_price
        self.average_price = average_price.replace("元/平", "")
        self.desc = desc


    def text(self):
        raise_or_fall = 0.0
        if "暂无" in self.comunity_average_price:
            raise_or_fall = 0.0
        else:
            raise_or_fall = (float(self.average_price) - float(self.comunity_average_price))/float(self.average_price)

        return self.district + "," + \
               self.area + "," + \
               self.name + "," + \
               self.initial_total_price + "," + \
               self.comunity_average_price + "," + \
               self.final_total_price + "," + \
               self.average_price + "," + \
               self.desc + "," + \
               str(raise_or_fall * 100) + "%"

