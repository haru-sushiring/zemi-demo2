import matplotlib.pyplot as plt
import japanize_matplotlib
import base64
from io import BytesIO
import datetime


class return_text():
    def sum_text(self):
        return '大口投資家のBTC移動量（合計）とBTCの価格'

    def buy_text(self):
        return 'ウォレットから取引所へ移動した量とBTCの価格'

    def sell_text(self):
        return '取引所からウォレットへ移動した量とBTCの価格'


def Output_Graph():
	buffer = BytesIO()
	plt.savefig(buffer, format="png")
	buffer.seek(0)
	img = buffer.getvalue()
	graph = base64.b64encode(img)
	graph = graph.decode("utf-8")
	buffer.close()
	return graph


rtc = return_text()
def Plot_Graph(x,y,z,judge):
    match judge:
        case 'sum':
            text = rtc.sum_text()
        case 'buy':
            text = rtc.buy_text()
        case 'sell':
            text = rtc.sell_text()
        case _:
            text = 'no text'

    plt.switch_backend("AGG")
    fig, ax1 = plt.subplots(1,1,figsize=(10,5))
    ax2 = ax1.twinx()
    ax1.plot(x,z,linestyle="solid",color="k")
    ax1.ticklabel_format(style='plain',axis='y') #軸を普通表記にする
    ax1.set_ylabel("price")
    ax2.bar(x,y)
    ax2.set_ylabel("amount")
    ax1.set_title(text)
    ax1.set_zorder(10)
    ax2.set_zorder(1)
    ax1.patch.set_alpha(0)
    handler1, label1 = ax1.get_legend_handles_labels()
    handler2, label2 = ax2.get_legend_handles_labels()
    ax1.legend(handler1+handler2,label1+label2,borderaxespad=0)
    fig.autofmt_xdate()
    plt.tight_layout()
    graph = Output_Graph()
    return graph