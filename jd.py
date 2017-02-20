# encoding=utf8
import warnings
warnings.filterwarnings("ignore")
import requests
import MySQLdb
import json
import time
import re
import os
import sys
import random
import urllib2
from pyquery import PyQuery
from sklearn.externals import joblib
import socket
socket.setdefaulttimeout(2)
import psutil

class JD(object):

	def __init__(self):
		self.db_config = {
			"host": "127.0.0.1",
			"port": 3306,
			"user": "root",
			"passwd": "root",
			"db": "jd"
		}
		self.db = self.init_mysql()
		self.cursor = self.db.cursor()
		self.cursor.execute("set names utf8")

		self.http_headers = {
			# "Connection": "keep-alive",
			# "Connection": "close",
			"User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36",
			"Accept-Encoding": "gzip, deflate, sdch"
		}
		self.httplib = requests.session()
		self.httplib.keep_alive = False
  
		self.goagent = {"http": "http://127.0.0.1:8087"}
		# self.proxy_list = [("127.0.0.1", 8087)]
		self.proxy_list = self.get_proxy()
		self.proxies = None

	def process_count(self):
		p_count = 0
		pids = psutil.pids()
		for pid in pids:
			try:
				p = psutil.Process(pid)
				exe = p.exe()
				cmd = p.cmdline()
				cmd = " ".join(cmd)
				if "jd.py" in cmd:
					# print pid, cmd[:30]
					p_count += 1
			except:
				pass
		return p_count
		
	def init_mysql(self):
		try:
			db = MySQLdb.connect(**self.db_config)
		except Exception as e:
			# print e
			del self.db_config["db"]
			db = MySQLdb.connect(**self.db_config)
			cursor = db.cursor()
			cursor.execute("""CREATE DATABASE IF NOT EXISTS `jd` /*!40100 COLLATE 'utf8_general_ci' */;""")
			db.commit()
			db.select_db("jd")
			self.cursor = cursor
			self.db = db
			self.create_table()
		return db

	def create_table(self):
		print "Create table"
		sql_cat = """CREATE TABLE `category` (
				`id` INT(11) NOT NULL AUTO_INCREMENT,
				`name` VARCHAR(64) NULL DEFAULT NULL,
				`url` VARCHAR(128) NULL DEFAULT NULL,
				`processed` TINYINT(4) NULL DEFAULT '0',
				PRIMARY KEY (`id`),
				UNIQUE INDEX `url` (`url`)
			)
			COLLATE='utf8_general_ci'
			ENGINE=InnoDB
		"""
		self.cursor.execute(sql_cat)
		self.db.commit()

		sql_item_price = """CREATE TABLE IF NOT EXISTS `item_price` (
				`id` BIGINT(20) NOT NULL AUTO_INCREMENT,
				`item_id` VARCHAR(50) NULL DEFAULT NULL,
				`date` VARCHAR(20) NULL DEFAULT NULL,
				`price` FLOAT NULL DEFAULT NULL,
				PRIMARY KEY (`id`),
				UNIQUE INDEX `item_id_date` (`item_id`, `date`)
			)
			COLLATE='utf8_general_ci'
			ENGINE=InnoDB;
		"""
		self.cursor.execute(sql_item_price)
		self.db.commit()

		sql_item_list = """CREATE TABLE IF NOT EXISTS `item_list` (
			`item_id` VARCHAR(50) NOT NULL DEFAULT '',
			PRIMARY KEY (`item_id`)
		)
		COLLATE='utf8_general_ci'
		ENGINE=InnoDB;
		"""
		self.cursor.execute(sql_item_list)
		self.db.commit()

	def check_proxy_1(self, proxy_list):
		ava_list = []
		test_url = "http://xueshu.baidu.com/"
		for host, port in proxy_list:
			host_port = "%s:%s" % (host, port)
			proxy = {
				"http": "http://%s" %(host_port),
				"https": "https://%s" %(host_port),
			}
			ret = False
			try:
				data = requests.get(test_url, verify=False, headers=self.http_headers, proxies=proxy, timeout=1.5)
				if "百度" in data:
					ret = True
					ava_list.append((host, port))
			except Exception as e:
				print e
				ret = False
			print "checking: %s ---> %s" % (host_port, str(ret))
		return ava_list

	def check_proxy(self, proxy_list):
		ava_list = []
		test_url = "http://www.baidu.com/"
		for host, port in proxy_list:
			ret = False
			host_port = "%s:%s" % (host, port)
			proxy = {
				"http": "http://%s" %(host_port),
				"https": "https://%s" %(host_port),
			}
			proxy_handler = urllib2.ProxyHandler(proxy)
			opener = urllib2.build_opener(proxy_handler)
			try:
				conn = opener.open(test_url, timeout=2.5)
				data = conn.read()
				if "百度" in data:
					ret = True
					ava_list.append((host, port))
			except Exception as e:
				# print e
				ret = False
			print "checking proxy: %s ---> %s" % (host_port, str(ret))
		return ava_list

	def get_proxy_online_1(self):
		url_list = [
			"http://www.kuaidaili.com/free/inha/",  # 国内高匿代理
			"http://www.kuaidaili.com/free/intr/",  # 国内普通代理
			"http://www.kuaidaili.com/free/outha/",  # 国外高匿代理
			"http://www.kuaidaili.com/free/outtr/"  # 国外普通代理
		]
		proxy_list = []
		for url in url_list:
			data = requests.get(url, headers=self.http_headers).content
			data = data.replace("\n", "").replace("\r", "")
			# print data
			if "Blocked by CC firewall" in data:
				data = requests.get(url, headers=self.http_headers, proxies=self.goagent).content
			# print data
			proxy_list += re.findall("""<td data-title="IP">(.+?)</td>\s*<td data-title="PORT">(.+?)</td>""", data)
		if not proxy_list:
			time.sleep(0.5)
			return self.get_proxy_online()
		return proxy_list

	def get_proxy_online_2(self):
		try:
			proxy_list = []
			url = "http://www.gatherproxy.com/zh/proxylist/country/?c=China"
			data = requests.get(url, headers=self.http_headers, proxies=self.goagent).content
			data = data.replace("\n", "").replace("\r", "")
			a_list = re.findall("""gp.insertPrx\((.+?)\);""", data)

			for proxy_info in a_list:
				proxy_info = json.loads(proxy_info)
				PROXY_HOST = proxy_info["PROXY_IP"]
				PROXY_PORT = proxy_info["PROXY_PORT"]
				PROXY_PORT = eval("0x%s" %PROXY_PORT)
				proxy_list.append((PROXY_HOST, PROXY_PORT))
		except:
			pass
		return proxy_list

	def get_proxy_online(self):
		proxy_list = []
		url = "http://proxy.ipcn.org/proxylist.html"
		req = urllib2.Request(url)
		req.add_header("Connection", "keep-alive")
		req.add_header("Cache-Control", "max-age=0")
		req.add_header("Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8")
		req.add_header("User-Agent",
					   "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/40.0.2214.115 Safari/537.36")
		req.add_header("Accept-Language", "zh-CN,zh;q=0.8")

		conn = urllib2.urlopen(req)
		data = conn.read()
		data = data.replace("\n", " ")
		alist = re.findall("(\d+\.\d+\.\d+\.\d+):(\d+)", data)
		for host, port in alist:
			# print host, port
			proxy_list.append((host, port))

		proxy_list = list(set(proxy_list))
		return proxy_list

	def get_proxy(self):
		file_name = "proxies.dat"
		if os.path.exists(file_name):
			proxy_list = joblib.load(file_name)
		else:
			proxy_list = self.get_proxy_online()
			proxy_list += self.get_proxy_online_1()
			proxy_list += self.get_proxy_online_2()
			proxy_list = list(set(proxy_list))
			proxy_list = self.check_proxy(proxy_list)
			joblib.dump(proxy_list, file_name, compress=3)
		proxy_list.append(("127.0.0.1", 8087))
		return proxy_list

	def switch_proxy(self):
		i = random.randint(-10, len(self.proxy_list) - 1)
		if i < 0:
			self.proxies = None
		else:
			host = self.proxy_list[i][0]
			port = self.proxy_list[i][1]
			self.proxies = {
				"http": "http://%s:%s" % (host, port),
				"https": "https://%s:%s" % (host, port),
			}
			print "Swicthing Proxy --> %s:%s" % (host, port)

	def proxy_requests(self, url, retry=5):
		try:
			# data = requests.get(url, verify=False, proxies=self.proxies, headers=self.http_headers).content
			# data = requests.get(url, headers=self.http_headers).content
			# conn = requests.get(url, headers=self.http_headers, timeout=2.0)
			# data = conn.content
			# conn.close()
			# data = self.httplib.get(url, headers=self.http_headers, timeout=2.0).content
			data = self.httplib.get(url, headers=self.http_headers, proxies=self.proxies, timeout=2.0).content
			return data
		except Exception as e:
			# print "proxy_requests: %d" %(retry)
			# print e
			if retry < 0:
				return None
			if retry >= 3:
				self.switch_proxy()
			return self.proxy_requests(url, retry=retry-1)

	def get_category(self):
		print "get_category"
		# https://list.jd.com/list.html?cat=12379,12380,12381
		url = "https://www.jd.com/allSort.aspx"
		data = requests.get(url, verify=False).content
		DOM = PyQuery(data)
		a_list = DOM("a")
		for i in range(len(a_list)):
			href = a_list.eq(i).attr("href")
			if href and "list.html" in href:
				# href = "https:%s" %(href)
				href = "http:%s" %(href)
				text = a_list.eq(i).text().encode("utf8")
				try:
					self.cursor.execute("insert into category (name, url) VALUES (%s, %s)", (text, href))
				except:
					pass
		self.db.commit()

		sql = "select id, name, url from category where processed = 0 ORDER BY id"
		self.cursor.execute(sql)
		rows = self.cursor.fetchall()
		return rows

	def get_items(self, cat_url, page=1, page_num=None, max_page=200):
		if page == 1:
			print "get_items"
		if (page_num and page_num < page) or page > max_page:
			return False
		url = "%s&page=%d&sort=sort_rank_asc&trans=1&JL=6_0_0#J_main" %(cat_url, page)
		url = url.replace("&jth=i", "")
		# print url
		print "-",
		retry = 5
		while retry:
			retry = retry -1
			data = self.proxy_requests(url)
			try:
				if page_num is None:
					"""# <em>共<b>106</b>页&nbsp;&nbsp;到第</em>"""
					page_num = data.split("<em>共<b>")[-1].split("</b>页&nbsp;&nbsp;到第</em>")[0]
					page_num = int(page_num)
					# print u"共%d页" %page_num

				dom = PyQuery(data)
				item_list = dom("div.j-sku-item")
				for i in range(len(item_list)):
					item = item_list.eq(i)
					item_id = item.attr("data-sku")
					# http://item.jd.com/10588446917.html
					# print "http://item.jd.com/%s.html" %item_id
					self.cursor.execute("replace into item_list (item_id) VALUES ('%s')" %item_id)
				break
			except:
				self.db.commit()
				return False

		self.db.commit()
		return page_num

	def init_price(self):
		date = time.strftime("%Y-%m-%d")
		sql = "select count(*) as C from item_price a where a.date = '%s' and a.price is null" %date
		self.cursor.execute(sql)
		rows = self.cursor.fetchall()
		NUM = rows[0][0]
		# if True:
		if NUM == 0:
			print "init_price"
			self.cursor.execute("select * from item_list")
			rows = self.cursor.fetchall()
			for index, row in enumerate(rows):
				item_id = row[0]
				sql = "insert into item_price (item_id, date, price) values (%s, %s, %s)"
				try:
					self.cursor.execute(sql, (item_id, date, None))
				except Exception as e:
					# print e
					pass
				if index % 100 == 0:
					self.db.commit()

			# JUST FOR RECORD
			sql = "insert into item_price (item_id, date, price) values (%s, %s, %s)"
			self.cursor.execute(sql, ("INITED", date, None))
			self.db.commit()

	def get_item_price(self, num_per_req=20, order="desc"):
		print "get_item_price"
		date = time.strftime("%Y-%m-%d")
		self.init_price()
		if self.process_count() >= 2:
			if order == "asc":
				order = "desc"
			else:
				order = "asc"
		self.cursor.execute("select id, item_id from item_price WHERE price is null ORDER BY id %s" %order)
		rows = self.cursor.fetchall()
		for index in range(0, len(rows), num_per_req):
			# print rows[index: index+num_per_req]
			# item_ids = ["J_"+r[1] for r in rows[index: index+num_per_req]]
			item_ids = []
			id_item_id = {}
			for row in rows[index: index+num_per_req]:
				id, item_id = row
				item_ids.append("J_%s" %item_id)
				id_item_id[item_id] = id

			item_ids_str = ",".join(item_ids)
			url = "https://p.3.cn/prices/mgets?skuIds=%s&type=1&area=22_1930_50949_52153.138431319&pdtk=&pduid=1370727125" % (item_ids_str)
			# print url
			data = self.proxy_requests(url)
			# print data
			while (not data or "pdos_captcha" in data):
				data = self.proxy_requests(url)

			data = json.loads(data)
			values = []
			for d in data:
				item_id = d["id"].replace("J_", "")
				id = id_item_id[item_id]
				price = d["p"]
				print id, item_id, price
				values.append([price, id])
				
			sql = "update item_price set price = %s WHERE id = %s"
			self.cursor.executemany(sql, values)
			
			if index % 100 == 0:
				self.db.commit()
		self.db.commit()

if __name__ == "__main__":

	jd = JD()

	if len(sys.argv) == 2:
		func = sys.argv[1]
		code = "jd.%s()" %func
		eval(code)
	else:
		category_list = jd.get_category()

		for id, name, url in category_list:
			url = url.replace("&jth=i", "")
			print "\n", id, name.decode("utf8"), url
			page_num = None
			page = 1
			while True:
				page_num = jd.get_items(url, page=page, page_num=page_num, max_page=40)
				page += 1
				if not page_num:
					break
			sql = "update category set processed = 1 WHERE id = %s"
			jd.cursor.execute(sql, (id,))
			jd.db.commit()
		
		jd.get_item_price()











