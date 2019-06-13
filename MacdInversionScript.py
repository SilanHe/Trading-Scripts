#!/usr/bin/env python3

from alpha_vantage.timeseries import TimeSeries
from alpha_vantage.techindicators import TechIndicators
import matplotlib.pyplot as plt
from datetime import datetime
from matplotlib.dates import DateFormatter
from matplotlib.pyplot import figure
import time

def get_watchlist():
	with open("watchlist.txt", "r") as f:    
		content = f.readlines()
	return [c[:-1] for c in content]

def sma(data, window):
	"""
	Calculates Simple Moving Average
	http://fxtrade.oanda.com/learn/forex-indicators/simple-moving-average
	"""
	if len(data) < window:
		return None
	return sum(data[-window:]) / float(window)

def ema(data, window):
	if len(data) < 2 * window:
		raise ValueError("data is too short")
	c = 2.0 / (window + 1)
	current_ema = sma(data[-window*2:-window], window)
	for value in data[-window:]:
		current_ema = (c * value) + ((1 - c) * current_ema)
	return current_ema

def get_slope(intersect,macd):

	if intersect == None:
		return 'No Inversion'
	elif intersect[1] == -1:
		return 'Fresh Inversion'
	
	#check to see how recent the inversion is
	time_since = len(macd) - intersect[-1]
	
	#check slope to see how bulish the inversion or bearish the inversion is
	macd_1 = macd[intersect[1]]
	macd_2 = macd[-1]
	
	slope = (macd_1 - macd_2)/(-1+intersect[1])
	
	if slope >= 1:
		return 'Strong Bullish Inversion. Days since: ' + time_since
	elif slope >= 0.2:
		return 'Bullish Inversion. Days since: ' + time_since
	elif slope > 0:
		return 'Weak Bullish Inversion. Days since: ' + time_since
	elif slope == 0:
		return 'Neutral Inversion. Days since: ' + time_since
	elif slope > -0.2:
		return 'Weak Bearish Inversion. Days since: ' + time_since
	elif slope > -1:
		return 'Bearish Inversion. Days since: ' + time_since
	elif slope <= -1:
		return 'Strong Bearish Inversion. Days since: ' + time_since

def generate_graph(data,macd_data,signal_line,ticker):
	# Get json object with the intraday data and another with  the call's metadata

	# main plot
	f, (ax1, ax2) = plt.subplots(2, 1, sharex=True)

	ax1.plot(list(data.index),list(data['4. close']),label='price')
	plt.title('Daily Time Series for %s' % ticker)

	plt.xticks(fontsize=8, rotation=30)
	plt.grid(True)

	# Don't allow the axis to be on top of your data
	ax1.legend()
	ax1.set_axisbelow(True)

	# Turn on the minor TICKS, which are required for the minor GRID
	ax1.minorticks_on()

	# Customize the major grid
	ax1.grid(which='major', linestyle='-', linewidth='0.5', color='red')
	# Customize the minor grid
	# ax.grid(which='minor', linestyle=':', linewidth='0.5', color='black')

	# Turn off the display of all ticks.
	ax1.tick_params(which='both', # Options for both major and minor ticks
					top='off', # turn off top ticks
					left='off', # turn off left ticks
					right='off',  # turn off right ticks
					bottom='off') # turn off bottom ticks

	ax1.xaxis.set_major_locator(plt.MaxNLocator(20))

	# the third plot under
	ax2.plot(macd_data['MACD'][-100:],label='macd')
	ax2.plot(signal_line,label='signal line')
	plt.xticks(fontsize=8, rotation=30)
	plt.grid(True)


	# Don't allow the axis to be on top of your data
	ax2.legend()
	ax2.set_axisbelow(True)

	# Turn on the minor TICKS, which are required for the minor GRID
	ax2.minorticks_on()

	# Customize the major grid
	ax2.grid(which='major', linestyle='-', linewidth='0.5', color='red')
	# Customize the minor grid
	# ax.grid(which='minor', linestyle=':', linewidth='0.5', color='black')

	# Turn off the display of all ticks.
	ax2.tick_params(which='both', # Options for both major and minor ticks
					top='off', # turn off top ticks
					left='off', # turn off left ticks
					right='off',  # turn off right ticks
					bottom='off') # turn off bottom ticksf

	ax2.xaxis.set_major_locator(plt.MaxNLocator(20))

	fig = plt.gcf()
	fig.set_size_inches(18.5, 10.5)

	date = datetime.today().strftime('%Y-%m-%d')

	fig.savefig('%s-%s.png' % (ticker,date), dpi=100)

	plt.close()

def get_intersection(macd,signal): 
	for i in range(2,100):
		# take 2 points from each the macd line and the signal line and check for intersection
		index = i * -1
		macd_1 = macd[index-1]
		macd_2 = macd[index]

		signal_1 = signal[index-1]
		signal_2 = signal[index]

		if macd_1 <= signal_1 and macd_2 >= signal_2 and macd_2 >= macd_1:
			#bullish inversion
			return (1,index)
		elif macd_1 >= signal_1 and macd_2 <= signal_2 and macd_2 <= macd_1:
			#bearish inversion
			return (-1,index)
	return None


ts = TimeSeries(key='HFHLQNBPIUBWH9UF', output_format='pandas')
ti = TechIndicators(key='HFHLQNBPIUBWH9UF', output_format='pandas')

tickers = get_watchlist()

k = dict()
try:

	for t in tickers:
		# get the data from the api
		print(t)

		data, meta_data = ts.get_daily(t, outputsize='compact')
		macd_data, macd_meta_data = ti.get_macd(t,fastperiod=5,slowperiod=35,signalperiod=5)
		#calculate custom signal line from the macd
		signal_line = [ema(list(macd_data['MACD'][-200:i]),5) for i in range(-100,0)]

		generate_graph(data,macd_data,signal_line,t)

		intersect = get_intersection(list(macd_data['MACD']),signal_line)
		slope = get_slope(intersect,list(macd_data['MACD']))
		k[t] = slope


		#not go over the threshold number of request a minute
		time.sleep(30)
except KeyError:
	print("ERROR: KeyError")

finally:
	#write the generated data to file for easy reading
	# Filename to append
	date = datetime.today().strftime('%Y-%m-%d')

	filename = "watchlist-%s.txt" % date

	# The 'a' flag tells Python to keep the file contents
	# and append (add line) at the end of the file.
	myfile = open(filename, 'w')

	#convert my data to string
	# sorted_k = sorted(k.items(), key=lambda kv: kv[1])
	content = '\n'.join("{!s}:{!s}".format(key,val) for (key,val) in k.items())

	# Add the line
	myfile.write(content)

	# Close the file
	myfile.close()

