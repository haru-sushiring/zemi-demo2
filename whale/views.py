from django.shortcuts import render


import time
import datetime
import math
import requests
import os
from dotenv import load_dotenv
import psycopg2

# api_key, db_urlの読み込み
load_dotenv()


### メイン処理
def main(self):

	#　インスタンス生成
	buy_alert_class = BuyAlertClass()
	sell_alert_class = SellAlertClass()
	tsc = TimeStampClass()
	rdbc = RegisterDBClass()

	# unix_timestamp = '1667000172'
	unix_timestamp = tsc.new_time_stamp()
	tsc.register_time_stamp(unix_timestamp)
	print(unix_timestamp)


	#
	# 無限ループ開始
	#

	t_end = time.time() + 60 * 62
	while time.time() < t_end:

	  unix_timestamp = tsc.return_old_time_stamp()
	  print('古いタイムスタンプを利用 : ' + str(unix_timestamp))
	  new_btc_json = return_api_json(unix_timestamp)

	  json_error_count = 0
	  while (new_btc_json == 'False'):
	    new_btc_json = return_api_json(unix_timestamp)
	    json_error_count += 1
	    if (json_error_count == 5):
	      	unix_timestamp = tsc.new_time_stamp()
	      	new_btc_json = return_api_json(unix_timestamp)
	    elif (json_error_count >= 10):
	      	print('jsonを取得できませんでした')
	      	break

	  json_result = new_btc_json['result']
	  while (json_result == 'error'):
	  	time.sleep(20)
	  	if (new_btc_json['message'] == 'usage limit reached'):
	  		print(new_btc_json['message'])
	  		time.sleep(20)
	  	new_btc_json = return_api_json(unix_timestamp)

	  btc_transactions_count = new_btc_json['count']
	  print('count : ' + str(btc_transactions_count))
	  while (btc_transactions_count == 0):
	    new_btc_json = return_api_json(unix_timestamp)
	    if (new_btc_json['result'] == 'error'):
	      	new_btc_json = return_api_json(unix_timestamp)
	    elif (new_btc_json['result'] == 'success'):
	      	btc_transactions_count = new_btc_json['count']
	    else:
	      	print('トランザクションエラー')

	  print('count : ' + str(btc_transactions_count))

	  comparison_time_stamp = 0
	  transactions_list = new_btc_json['transactions']
	  for transaction in transactions_list:
	    new_time_stamp = transaction['timestamp']

	    if (comparison_time_stamp == 0):
	    	comparison_time_stamp = new_time_stamp
	    	tsc.register_time_stamp(new_time_stamp)

	    if (comparison_time_stamp != new_time_stamp):
	    	tsc.register_time_stamp(comparison_time_stamp)
	    	break

	    btc_id = transaction['id']
	    btc_from = transaction['from']['owner_type']
	    # print('btc_from : ' + btc_from)
	    btc_to = transaction['to']['owner_type']
	    # print('btc_to : ' + btc_to)
	    btc_amount = transaction['amount']

	    if (btc_from == 'exchange' and btc_to == 'unknown'):
		    buy_alert_class.buy_alert(btc_amount)
		    timestamp = tsc.exchange_time_stamp(new_time_stamp)
		    rdbc.db_register_buy(timestamp, btc_amount)
	    if (btc_from == 'unknown' and btc_to == 'exchange'):
	    	sell_alert_class.sell_alert(btc_amount)
	    	timestamp = tsc.exchange_time_stamp(new_time_stamp)
	    	rdbc.db_register_sell(timestamp, btc_amount)


###
class TimeStampClass:

  def __init__(self):
    self.old_time_stamp = 0

  def new_time_stamp(self):
    return math.floor(time.time())

  def register_time_stamp(self, new_time_stamp):
    print('古いタイムスタンプを登録 : ' + str(new_time_stamp))
    self.old_time_stamp = new_time_stamp

  def return_old_time_stamp(self):
    return self.old_time_stamp

  def exchange_time_stamp(self, timestamp):
    return datetime.datetime.fromtimestamp(timestamp, datetime.timezone(datetime.timedelta(hours=9)))



###
def return_api_json(unix_timestamp):
    api_url = 'https://api.whale-alert.io/v1/transactions?'
    payload = {
        'api_key': os.environ['API_KEY'],
        'start': unix_timestamp,
        'currency': 'btc'
        }

    try:
    	time.sleep(15)
    	r = requests.get(api_url, params=payload)
    	new_btc_json = r.json()
    except r.JSONDecodeError:
    	print('JSONDecodeError')
    	return 'False'

    return new_btc_json


###
class BuyAlertClass:
  def buy_alert(self, btc_amount):
    print('buy_amount：' + str(btc_amount))
    # ここでdb登録（日付、sum_buy_alert、id（idの合計数がアラートの回数だから））


###
class SellAlertClass:
  def sell_alert(self, btc_amount):
    print('sell_amount：' + str(btc_amount))
    # ここでdb登録（日付、sum_sell_alert、id（idの合計数がアラートの回数だから））


###
class RegisterDBClass:
	def __init__(self):
		self.DATABASES_URL = os.environ['DATABASE_URL']

	def db_register_buy(self, timestamp, btc_amount):
		amount = btc_amount
		judge = 'buy'
		with psycopg2.connect(self.DATABASES_URL) as conn:
			with conn.cursor() as curs:
				curs.execute(
					"INSERT INTO whale(timestamp,amount,judge) VALUES(%s, %s, %s)", (timestamp, amount, judge))

		print('db登録しました buy')

	def db_register_sell(self, timestamp, btc_amount):
		amount = btc_amount
		judge = 'sell'
		with psycopg2.connect(self.DATABASES_URL) as conn:
			with conn.cursor() as curs:
				curs.execute(
					"INSERT INTO whale(timestamp,amount,judge) VALUES(%s, %s, %s)", (timestamp, amount, judge))

		print('db登録しました sell')


###
if __name__ == '__main__':
	main()