from django.shortcuts import render
from django.http import HttpResponse

import pandas as pd

import os
import psycopg2
from dotenv import load_dotenv

# db_urlの読み込み
load_dotenv()

# def index(request):
# 	return render(request, 'base.html')

from django.views.generic import TemplateView
from whale import models
from . import graph


class Index(TemplateView):

	template_name = 'base.html'

	def get_context_data(self, **kwargs):

		qs = models.Whale.objects.all()
		x  = [x.timestamp for x in qs]
		y  = [y.amount for y in qs]
		char = graph.Plot_Graph(x,y)

		context = super().get_context_data(**kwargs)
		context['char'] = char
		return context

	def get(self, request, *args, **kwargs):
		return super().get(request, *args, **kwargs)



# def index(request):
#     # 変数設定
#     # test = "Hello World"
#     # params = {"message_me": "Hello World"}
#     db_test = db_get()
#     params = {"message_me": db_test}
#     # 出力
#     return render(request,'base.html',context=params)

# def db_get():
# 	DATABASE_URL = os.environ['DATABASE_URL']
# 	with psycopg2.connect(DATABASE_URL) as conn:
# 	    with conn.cursor() as curs:
# 	        curs.execute("SELECT * FROM whale")
# 	        return_database = curs.fetchall()
# 	        print(return_database)
# 	        print(type(return_database))
# 	        print(type(return_database[0]))

# 	return return_database






# def db_get():
# 	conn = psycopg2.connect(
#         host=XXX,
#         dbname=XXX,
#         user=XXX,
#         password=XXX,
#     )


# def db_get():
# 	DATABASE_URL = os.environ['DATABASE_URL']
# 	with psycopg2.connect(DATABASE_URL) as conn:
# 		query = """SELECT * FROM whale"""
# 		df = pd.read_sql(query, con=conn)
# 		return_database = df.head()
# 	    # with conn.cursor() as curs:
# 	    #     curs.execute("SELECT * FROM whale")
# 	        # return_database = curs.fetchall()
# 	        # print(return_database)
# 	        # print(type(return_database))
# 	        # print(type(return_database[0]))

# 	return return_database

