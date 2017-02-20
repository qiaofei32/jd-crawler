#encoding=utf8
import os
import sys
import web
from jd import JD

urls = (
	'/(.*)', 'Index',
	'/(.*)/(css|img|js)/(.*)', 'Static',
	'/(css|img|js)/(.*)', 'Static',
)

jd_api = JD()
jd_db = jd_api.db
cursor = jd_api.cursor

def notfound():
	return web.notfound("Sorry, the page you were looking for was not found.")

class Static:
	def GET(self, *args):
		dir, name = args[-2:]
		dir_path = 'templates/%s/' %dir
		ext = name.split(".")[-1]
		cType = {
			"css": "text/css",
			"png": "images/png",
			"jpg": "images/jpeg",
			"gif": "images/gif",
			"ico": "images/x-icon",
			"js" : "text/javascrip",
		}
		if name in os.listdir(dir_path):
			web.header("Content-Type", cType[ext])
			file_path = '%s/%s' %(dir_path, name)
			return open(file_path, "rb").read()
		else:
			raise web.notfound()

class Index:
	def GET(self, _):
		params = web.input()
		# web.debug(params)
		date_list = []
		price_list = []
		price_info_dict = {
			"date": "['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']",
			"price": "[7.0, 6.9, 9.5, 14.5, 18.2, 21.5, 25.2, 26.5, 23.3, 18.3, 13.9, 9.6]"
		}
		try:
			item_id = params.item_id.encode("utf8")
			if not item_id:
				return render.index(price_info_dict)
			result = cursor.execute("select * from item_price where item_id = '%s' ORDER BY date desc" %item_id)
			rows = cursor.fetchall()
			for row in rows:
				# print row
				id, item_id, date, price = row
				date_list.append(date,)
				price_list.append(price)
				price_info_dict["date"] = str(date_list)
			price_info_dict["price"] = str(price_list)
			return render.index(price_info_dict)
		except:
			return render.index(price_info_dict)

app = web.application(urls, globals())
render = web.template.render('templates/')
app.notfound = notfound

if __name__ == '__main__':
	app.run()