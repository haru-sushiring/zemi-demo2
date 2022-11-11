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

    #　インスタンス
    api = APIClass()
    alert_class = AlertClass()
    tsc = TimeStampClass()
    rdbc = RegisterDBClass()

    # unix_timestamp = '1667000172'
    unix_timestamp = tsc.new_time_stamp()
    tsc.register_time_stamp(unix_timestamp)
    print(unix_timestamp)


    #
    # 無限ループ開始
    #

    # t_end = time.time() + 60 * 60*24
    t_end = time.time() + 60 * 60*2
    while time.time() < t_end:

      unix_timestamp = tsc.return_old_time_stamp()
      print('古いタイムスタンプを利用 : ' + str(unix_timestamp))

      time.sleep(15)
      api_url = 'https://api.whale-alert.io/v1/transactions?'
      payload = api.whale_api_param(unix_timestamp)
      # r = requests.get(api_url, params=payload)
      # new_btc_json = api.return_api_json(unix_timestamp)

      error_flg = 0
      while (error_flg == 0):
          r = requests.get(api_url, params=payload)
          # print(r.json())
          match r.json():
            case {"result": 'error', "message": error}:
                print(r.json())
                print(f"Response error!: {error}")
                time.sleep(20)
                unix_timestamp = tsc.new_time_stamp()
                payload = api.whale_api_param(unix_timestamp)
            case {"result": 'success', "count": count} if count == 0:
                time.sleep(15)
                # print(r.json())
            case {"result": 'success', "count": count} if count > 0:
                error_flg = 1
                # print('トランザクションが1個以上ある')
            case _:
                print('不明なエラー jsonが取得できませんでした')



      print('ok')
      new_btc_json = r.json()


      btc_transactions_count = new_btc_json['count']
      print('count : ' + str(btc_transactions_count))


      # 同じタイムスタンプのトランザクションの値を処理する
      comparison_time_stamp = 0
      sum_buy_btc_amount = 0
      sum_sell_btc_amount = 0
      btc_jpy_price = 0
      transactions_list = new_btc_json['transactions']

      # 同じタイムスタンプのトランザクションがある間、処理を行う
      for transaction in transactions_list:
        new_time_stamp = transaction['timestamp']

        # 新しいタイムスタンプのトランザクションの時、初期化処理を行う
        if (comparison_time_stamp == 0):
            comparison_time_stamp = new_time_stamp
            tsc.register_time_stamp(new_time_stamp)
            timestamp = tsc.exchange_time_stamp(new_time_stamp) # タイムスタンプを日本時間に直す
            btc_jpy_price = api.btc_jpy_price() # BTCの価格を取得する

        # 新しく取得したトランザクションが前回のトランザクションのタイムスタンプと違う場合、breakして新しいトランザクションを取得する
        if (comparison_time_stamp != new_time_stamp):
            #1つ前のタイムスタンプを利用して新しいjsonデータを取得するために、関数に登録しておく
            tsc.register_time_stamp(comparison_time_stamp)
            # 同じタイムスタンプの時の、BTC移動の合計量とBTC価格をデータベースに登録する
            if (sum_buy_btc_amount > 0):
                move_side = 'buy'
                rdbc.db_register(timestamp, sum_buy_btc_amount, btc_jpy_price, move_side)
            if (sum_sell_btc_amount > 0):
                move_side = 'sell'
                rdbc.db_register(timestamp, sum_sell_btc_amount, btc_jpy_price, move_side)
            break

        btc_id = transaction['id']
        btc_from = transaction['from']['owner_type']
        btc_to = transaction['to']['owner_type']
        btc_amount = transaction['amount']

        if (btc_from == 'exchange' and btc_to == 'unknown'):
            alert_class.buy_alert(btc_amount)
            sum_buy_btc_amount += btc_amount
            print(sum_buy_btc_amount)

        if (btc_from == 'unknown' and btc_to == 'exchange'):
            alert_class.sell_alert(btc_amount)
            sum_sell_btc_amount += btc_amount
            print(sum_sell_btc_amount)


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
class APIClass:
    def whale_api_param(self, unix_timestamp):
        payload = {
            'api_key': os.environ['API_KEY'],
            'start': unix_timestamp,
            'currency': 'btc'
            }

    #     time.sleep(15)
    #     r = requests.get(api_url, params=payload)

    #     # except r.JSONDecodeError:
    #     #   print('JSONDecodeError')
    #     #   return 'False'

        return payload


    def btc_jpy_price(self):
        api_url = 'https://api.excelapi.org/crypto/rate?'
        payload = {
            'pair': 'btc-jpy'
            }

        btc_jpy_price = requests.get(api_url, params=payload)
        return btc_jpy_price.json()


###
class AlertClass:
  def buy_alert(self, btc_amount):
    print('buy_amount：' + str(btc_amount))

  def sell_alert(self, btc_amount):
    print('sell_amount：' + str(btc_amount))



###
class RegisterDBClass:
    def __init__(self):
        self.DATABASES_URL = os.environ['DATABASE_URL']

    def db_register(self, timestamp, btc_amount, btc_jpy_price, move_side):
        amount = btc_amount
        price = btc_jpy_price
        move = move_side
        with psycopg2.connect(self.DATABASES_URL) as conn:
            with conn.cursor() as curs:
                curs.execute(
                    "INSERT INTO whale(timestamp,amount,price,move) VALUES(timezone('JST' ,%s), %s, %s, %s)", (timestamp, amount, price, move))

        print('db登録しました ' + move)


###
if __name__ == '__main__':
    main()