#!/usr/bin/env python
# coding=utf-8
# author: zengyuetian
# 爬取二手房数据的爬虫派生类


import re
import json
import threadpool
from user_agent import generate_user_agent
from bs4 import BeautifulSoup
from lib.item.chengjiao import *
from lib.zone.city import get_city
from lib.spider.base_spider import *
from lib.utility.date import *
from lib.utility.path import *
from lib.zone.area import *
from lib.utility.log import *
import lib.utility.version



class ChengJiao_Spider(BaseSpider):
    def collect_area_chengjiao_data(self, city_name, area_name, fmt="csv"):
        """
        对于每个板块,获得这个板块下所有二手房最新交易的信息
        并且将这些信息写入文件保存
        :param city_name: 城市
        :param area_name: 板块
        :param fmt: 保存文件格式
        :return: None
        """
        district_name = area_dict.get(area_name, "")
        csv_file = self.today_path + "/{0}_{1}.csv".format(district_name, area_name)
        with open(csv_file, "w") as f:
            # 开始获得需要的板块数据
            chengjiaos = self.get_area_chengjiao_info(city_name, area_name)
            # 锁定，多线程读写
            if self.mutex.acquire(1):
                self.total_num += len(chengjiaos)
                # 释放
                self.mutex.release()
            if fmt == "csv":
                for chengjiao in chengjiaos:
                    # print(date_string + "," + xiaoqu.text())
                    f.write(self.date_string + "," + chengjiao.text() + "\n")
        print("Finish crawl area: " + area_name + ", save data to : " + csv_file)

    
    def get_area_chengjiao_info(self, city_name, area_name):
        """
        通过爬取页面获得城市指定版块的二手房最新交易信息
        :param city_name: 城市
        :param area_name: 版块
        :return: 二手房交易数据列表
        """
        # total_page = 1
        district_name = area_dict.get(area_name, "")
        # 中文区县
        chinese_district = get_chinese_district(district_name)
        # 中文版块
        chinese_area = chinese_area_dict.get(area_name, "")

        chengjiao_list = list()
        page = 'https://{0}.{1}.com/chengjiao/{2}/'.format(city_name, SPIDER_NAME, area_name)
        # 打印版块页面地址
        #print(page)
        headers = create_headers()
        #headers = {'User-Agent':generate_user_agent(device_type="desktop", os=('mac','linux'))}
        response = requests.get(page, timeout=10, headers=headers)
        html = response.content
        soup = BeautifulSoup(html, "lxml")
        ul_content = soup.find('ul', class_='listContent')

        if ul_content == None:
            return chengjiao_list

        chengjiao_date_str = ''
        for li_children in ul_content.children:
            chengjiao_page = li_children.a['href']
            #print(chengjiao_page)
            # 访问成交页面
            # chengjiao_headers = {'User-Agent':generate_user_agent(device_type="desktop", os=('mac','linux'))}
            chengjiao_headers = create_headers()
            chengjiao_response = requests.get(chengjiao_page, timeout=10, headers=chengjiao_headers)
            chengjiao_html = chengjiao_response.content
            chengjiao_soup = BeautifulSoup(chengjiao_html, "lxml")

            # 确认成交日期
            date_temp = chengjiao_soup.find('div', class_='house-title').div.span.get_text().replace(' 成交', '')
            if chengjiao_date_str == '':
                chengjiao_date_str = date_temp
            elif date_temp != chengjiao_date_str:
                break

            # 获取交易具体情况
            temp_soup = chengjiao_soup.find('div', class_='house-title')
            desc = temp_soup.div.h1.get_text()
            name  = desc.split(' ')[0]
            final_total_price = chengjiao_soup.find('div', class_='price').span.get_text()
            average_price = chengjiao_soup.find('div', class_='price').get_text().replace(final_total_price, "")
            initial_total_price = chengjiao_soup.find('div', class_='msg').span.label.get_text() + "万"

            # 再次通过rid&hid获取具体小区信息JSON结构体
            rid = temp_soup.attrs['data-lj_action_housedel_id']
            hid = temp_soup.attrs['data-lj_action_resblock_id']
            resblock_page = 'https://{0}.{1}.com/chengjiao/resblock?hid={2}&rid={3}'.format(city_name, SPIDER_NAME, hid, rid)
            resblock_headers = create_headers()
            # resblock_headers = {'User-Agent':generate_user_agent(device_type="desktop", os=('mac','linux'))}
            resblock_response = requests.get(resblock_page, timeout=10, headers=resblock_headers)
            comunity_average_price = str(json.loads(resblock_response.content)["data"]["resblock"]["unitPrice"]) + '元/平'
            
            chengjiao = ChengJiao(chinese_district, chinese_area, name, initial_total_price, final_total_price, average_price, comunity_average_price, desc)
            chengjiao_list.append(chengjiao)

        return chengjiao_list



    def start(self):
        city = get_city()
        self.today_path = create_date_path("{0}/chengjiao".format(SPIDER_NAME), city, self.date_string)

        t1 = time.time()  # 开始计时

        # 获得城市有多少区列表, district: 区县
        districts = get_districts(city)
        print('City: {0}'.format(city))
        print('Districts: {0}'.format(districts))

        # 获得每个区的板块, area: 板块
        areas = list()
        for district in districts:
            areas_of_district = get_areas(city, district)
            print('{0}: Area list:  {1}'.format(district, areas_of_district))
            # 用list的extend方法,L1.extend(L2)，该方法将参数L2的全部元素添加到L1的尾部
            areas.extend(areas_of_district)
            # 使用一个字典来存储区县和板块的对应关系, 例如{'beicai': 'pudongxinqu', }
            for area in areas_of_district:
                area_dict[area] = district
        #print("Area:", areas)
        #print("District and areas:", area_dict)

        # 准备线程池用到的参数
        nones = [None for i in range(len(areas))]
        city_list = [city for i in range(len(areas))]
        args = zip(zip(city_list, areas), nones)
        # areas = areas[0: 1]   # For debugging

        # 针对每个板块写一个文件,启动一个线程来操作
        pool_size = thread_pool_size
        # pool_size = 1
        pool = threadpool.ThreadPool(pool_size)
        my_requests = threadpool.makeRequests(self.collect_area_chengjiao_data, args)
        [pool.putRequest(req) for req in my_requests]
        pool.wait()
        pool.dismissWorkers(pool_size, do_join=True)  # 完成后退出

        # 计时结束，统计结果
        t2 = time.time()
        print("Total crawl {0} areas.".format(len(areas)))
        print("Total cost {0} second to crawl {1} data items.".format(t2 - t1, self.total_num))


if __name__ == '__main__':
    pass