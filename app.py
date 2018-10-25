from flask import *
import pandas as pd
import datetime
from datetime import timedelta
pd.core.common.is_list_like = pd.api.types.is_list_like
import pandas_datareader.data as web
import pandas_highcharts.core

import os
from flask import Flask, flash, request, redirect, url_for
from werkzeug.utils import secure_filename
#from flask import send_from_directory

import talib
from talib import abstract
#from talib import MA_Type
#from talib.abstract import *
SMA = abstract.SMA
STOCH = abstract.STOCH
RSI = abstract.RSI
MACD = abstract.MACD
BBANDS = abstract.BBANDS
SAR = abstract.SAR
CDLENGULFING = abstract.CDLENGULFING

base = os.path.dirname(__file__)
UPLOAD_FOLDER = os.path.join(base, 'uploads')
ALLOWED_EXTENSIONS = set(['csv', 'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])

app = Flask(__name__)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

today = pd.to_datetime('today').strftime("%Y, %m, %d")
yt = datetime.datetime.today() - timedelta(days=365)
yeartoday = yt.strftime('%Y, %m, %d')

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def screen_second(csv, start, end):
    df = pd.DataFrame(index=['Ticker'],
                      columns=['Domain', 'Index', 'Date', '+-1%SMA50', '+-2%SMA150', 'stoch 14-6-6', 'stoch 5-3-3',
                               'RSI 14', 'RSI 10', 'MACD', 'BB', 'SAR', 'Engulfing', '+', 'Y_MA20+', 'M_MA20+'])

    inp = pd.read_csv(csv)
    syms = inp['Ticker'].tolist()
    inp.set_index('Ticker', inplace=True)

    for sym in syms:
        try:
            stock = web.DataReader(sym, 'robinhood', start, end)
            stock['close_price'] = stock['close_price'].apply(pd.to_numeric)
            stock['high_price'] = stock['high_price'].apply(pd.to_numeric)
            stock['low_price'] = stock['low_price'].apply(pd.to_numeric)
            stock['open_price'] = stock['open_price'].apply(pd.to_numeric)

            df.loc[sym] = ['', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '']

            stock['SMA50'] = SMA(stock, timeperiod=50, price=['close_price'])
            stock['SMA150'] = SMA(stock, timeperiod=150, price=['close_price'])
            stock[['slowk14', 'slowd14']] = STOCH(stock, 14, 6, 0, 6, 0, prices=['high_price', 'low_price', 'close_price'])
            stock[['slowk', 'slowd']] = STOCH(stock, 5, 3, 0, 3, 0, prices=['high_price', 'low_price', 'close_price'])
            stock['RSI14'] = RSI(stock, timeperiod=14, price=['close_price'])
            stock['RSI10'] = RSI(stock, timeperiod=10, price=['close_price'])
            stock[['macd', 'macdsignal', 'macdhist']] = MACD(stock, fastperiod=12, slowperiod=26, signalperiod=9,
                                                                 price=['close_price'])
            stock[['upper', 'middle', 'lower']] = BBANDS(stock, 20, 2, 2, price=['close_price'])
            stock['SAR'] = SAR(stock, acceleration=0.02, maximum=0.2, prices=['high_price', 'low_price'])
                # stock['SMA20'] = SMA(stock, timeperiod = 20, price = ['Adj Close'])
            stock['Engulfing'] = CDLENGULFING(stock, prices=['open_price', 'high_price', 'low_price', 'close_price'])

            if stock['macd'].iloc[-1] > 0 and stock['macd'].iloc[-1] > stock['macdsignal'].iloc[-1]:
                df.at[sym, 'MACD'] = '+x'
                df.at[sym, 'Domain'] = inp.at[sym, 'Domain']
                df.at[sym, 'Index'] = inp.at[sym, 'Index']
                df.at[sym, 'Date'] = inp.at[sym, 'Date']
                df.at[sym, '+'] = inp.at[sym, '+']
                df.at[sym, 'Y_MA20+'] = inp.at[sym, 'Y_MA20+']
                df.at[sym, 'M_MA20+'] = inp.at[sym, 'M_MA20+']

            if stock['macd'].iloc[-1] < 0 and stock['macd'].iloc[-1] > stock['macdsignal'].iloc[-1]:
                df.at[sym, 'MACD'] = '-x'
                df.at[sym, 'Domain'] = inp.at[sym, 'Domain']
                df.at[sym, 'Index'] = inp.at[sym, 'Index']
                df.at[sym, 'Date'] = inp.at[sym, 'Date']
                df.at[sym, '+'] = inp.at[sym, '+']
                df.at[sym, 'Y_MA20+'] = inp.at[sym, 'Y_MA20+']
                df.at[sym, 'M_MA20+'] = inp.at[sym, 'M_MA20+']

            if stock['macd'].iloc[-1] > 0 and stock['macd'].iloc[-1] < stock['macdsignal'].iloc[-1]:
                df.at[sym, 'MACD'] = '+o'
                df.at[sym, 'Domain'] = inp.at[sym, 'Domain']
                df.at[sym, 'Index'] = inp.at[sym, 'Index']
                df.at[sym, 'Date'] = inp.at[sym, 'Date']
                df.at[sym, '+'] = inp.at[sym, '+']
                df.at[sym, 'Y_MA20+'] = inp.at[sym, 'Y_MA20+']
                df.at[sym, 'M_MA20+'] = inp.at[sym, 'M_MA20+']

            if stock['macd'].iloc[-1] < 0 and stock['macd'].iloc[-1] < stock['macdsignal'].iloc[-1]:
                df.at[sym, 'MACD'] = '-o'
                df.at[sym, 'Domain'] = inp.at[sym, 'Domain']
                df.at[sym, 'Index'] = inp.at[sym, 'Index']
                df.at[sym, 'Date'] = inp.at[sym, 'Date']
                df.at[sym, '+'] = inp.at[sym, '+']
                df.at[sym, 'Y_MA20+'] = inp.at[sym, 'Y_MA20+']
                df.at[sym, 'M_MA20+'] = inp.at[sym, 'M_MA20+']

            if stock['close_price'].iloc[-1] > stock['SAR'].iloc[-1]:
                df.at[sym, 'SAR'] = 'x'

            if stock['close_price'].iloc[-1] < stock['SAR'].iloc[-1]:
                df.at[sym, 'SAR'] = 'o'

            if stock['close_price'].iloc[-1] <= stock['SMA50'].iloc[-1] * 1.01 and stock['close_price'].iloc[-1] >= \
                            stock['SMA50'].iloc[-1] - (stock['SMA50'].iloc[-1] * 0.01):
                df.at[sym, '+-1%SMA50'] = 'x'

            if stock['close_price'].iloc[-1] <= stock['SMA150'].iloc[-1] * 1.02 and stock['close_price'].iloc[-1] >= \
                            stock['SMA150'].iloc[-1] - (stock['SMA50'].iloc[-1] * 0.02):
                df.at[sym, '+-2%SMA150'] = 'x'

            if stock['slowk'].iloc[-1] < 20:
                df.at[sym, 'stoch 5-3-3'] = 'x'

            if stock['slowk'].iloc[-1] > 80:
                df.at[sym, 'stoch 5-3-3'] = 'o'

            if stock['slowk14'].iloc[-1] < 20:
                df.at[sym, 'stoch 14-6-6'] = 'x'

            if stock['slowk14'].iloc[-1] > 80:
                df.at[sym, 'stoch 14-6-6'] = 'o'

            if stock['RSI10'].iloc[-1] < 30:
                df.at[sym, 'RSI 10'] = 'x'

            if stock['RSI10'].iloc[-1] > 70:
                df.at[sym, 'RSI 10'] = 'o'

            if stock['RSI14'].iloc[-1] < 30:
                df.at[sym, 'RSI 14'] = 'x'

            if stock['RSI14'].iloc[-1] > 70:
                df.at[sym, 'RSI 14'] = 'o'

            if stock['low_price'].iloc[-1] < stock['lower'].iloc[-1]:
                df.at[sym, 'BB'] = 'x'

            if stock['high_price'].iloc[-1] > stock['upper'].iloc[-1]:
                df.at[sym, 'BB'] = 'o'

            if stock['Engulfing'].iloc[-1] == 100:
                df.at[sym, 'Engulfing'] = 'x'

            if stock['Engulfing'].iloc[-1] == -100:
                df.at[sym, 'Engulfing'] = 'o'

        except Exception as e:
            print('Could not load:', sym, e)
            continue
        #else:
            #break

    return df

@app.route("/")
def form():
    return render_template('form.html')

@app.route('/', methods=['POST'])
def form_post():
    text = request.form['input1']
    sym = text.upper()

    text = request.form['input2']
    index = text.upper()

    yt = datetime.datetime.today() - datetime.timedelta(days=365)
    start = yt
    end = datetime.datetime.now()

    try:

        df = web.DataReader(sym, 'robinhood', start, end)
        index = web.DataReader(index, 'robinhood', start, end)
        index.reset_index(inplace=True)
        index.set_index([index.columns[1]], inplace=True)

        df.reset_index(inplace=True)
        df.set_index([df.columns[1]], inplace=True)
        df['close_price'] = df['close_price'].apply(pd.to_numeric)

        index['close_price'] = index['close_price'].apply(pd.to_numeric)

        rsa_t = ((df['close_price'].iloc[0]) / (index['close_price'].iloc[0]))
        r = 100 / rsa_t
        index['rsa_r'] = ((((df['close_price'] / index['close_price']) * r)) - 100)

        c = 100 / (df['close_price'].iloc[0])
        df['close_price'] = (df['close_price'] * c) - 100

        ci = 100 / (index['close_price'].iloc[0])
        index['close_price'] = (index['close_price'] * ci) - 100

        df_syms = pd.concat([df['close_price'], index['close_price']], axis=1, keys=[sym, 'Index'])
        df_rsa = pd.concat([index['rsa_r']], axis=1, keys=[sym + ' RSA'])

        chart = pandas_highcharts.core.serialize(df_syms, render_to='my-chart', output_type='json', title = 'Index vs. Stock')
        chart1 = pandas_highcharts.core.serialize(df_rsa, render_to='my-chart1', output_type='json', title = 'RSA')

        return render_template('chart.html', chart = chart, chart1 = chart1)

    except:
        return render_template('load_error.html', name = 'error')



@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # if user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            return redirect(url_for('uploaded_file',
                                        filename=filename))

    return render_template('upload.html', name='Upload Csv')


@app.route('/uploads/<filename>', methods=['GET', 'POST'])
def uploaded_file(filename):
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if request.method == 'POST':
        data = screen_second(file_path, yeartoday, today)
        return render_template('data_table.html', name=filename + today, data=data.to_json())
    return render_template('screen.html', name=filename)



if __name__ == "__main__":
    app.run(debug=True)

