#!/usr/bin/env python

"""
Example for Implied Volatility using the NAG Library for Python
Finds implied volatilities of the Black Scholes equation using specfun.opt_imp_vol
Data needs to be downloaded from:
http://www.cboe.com/delayedquote/QuoteTableDownload.aspx
Make sure to download data during CBOE Trading Hours.

Updated for NAG Library for Python Mark 27.1
"""

try:
    import os,sys
    import pandas
    import numpy as np
    import matplotlib.pylab as plt
    import warnings
    from naginterfaces.library import specfun, fit
    from naginterfaces.base import utils
    from matplotlib import cm
    from mpl_toolkits.mplot3d import axes3d

except ImportError as e:
    print("Could not import the following module. Do you have a working installation of the NAG Library for Python?")
    print(e)
    sys.exit(1)

__author__ = "Edvin Hopkins, John Morrissey and Brian Spector"
__copyright__ = "Copyright 2021, The Numerical Algorithms Group Inc"
__email__ = "support@nag.co.uk"

# Set to hold expiration dates
dates = []

cumulative_month = {'Jan': 31, 'Feb': 57, 'Mar': 90,
                    'Apr': 120, 'May': 151, 'Jun': 181,
                    'Jul': 212, 'Aug': 243, 'Sep': 273,
                    'Oct': 304, 'Nov': 334, 'Dec': 365}


def main():

    try:
        if(len(sys.argv)>1):
            QuoteData = sys.argv[1]
        else:
            QuoteData = 'QuoteData.dat'

        qd = open(QuoteData, 'r')
        qd_head = []
        qd_head.append(qd.readline())
        qd_head.append(qd.readline())
        qd.close()
    except:
        sys.stderr.write("Usage: implied_volatility.py QuoteData.dat\n")
        sys.stderr.write("Couldn't read QuoteData")
        sys.exit(1)

    print("Implied Volatility for %s %s" % (qd_head[0].strip(), qd_head[1]))

    # Parse the header information in QuotaData
    first = qd_head[0].split(',')
    second = qd_head[1].split()
    qd_date = qd_head[1].split(',')[0]
    
    company = first[0]
    underlyingprice = float(first[1])
    month, day = second[:2]
    today = cumulative_month[month] + int(day) - 30
    current_year = int(second[2])

    def getExpiration(x):
        monthday = x.split()
        adate = monthday[0] + ' ' + monthday[1]
        if adate not in dates:
            dates.append(adate)
        return (int(monthday[0]) - (current_year % 2000)) * 365 + cumulative_month[monthday[1]]

    def getStrike(x):
        monthday = x.split()
        return float(monthday[2])

    data = pandas.io.parsers.read_csv(QuoteData, sep=',', header=2, na_values=' ')

    # Need to fill the NA values in dataframe
    data = data.fillna(0.0)

    # Let's look at data where there was a recent sale 
    data = data[(data['Last Sale'] > 0) | (data['Last Sale.1'] > 0)]

    # Get the Options Expiration Date
    exp = data.Calls.apply(getExpiration)
    exp.name = 'Expiration'

    # Get the Strike Prices
    strike = data.Calls.apply(getStrike)
    strike.name = 'Strike'

    data = data.join(exp).join(strike)
    
    print("Number of data points found: {}\n".format(len(data.index)))
        
    print('Calculating Implied Vol of Calls...')
    r = np.zeros(len(data.index))
    t = (data.Expiration - today)/365.0
    s0 = np.full(len(data.index),underlyingprice)
    pCall= (data.Bid + data.Ask) / 2
    
    # A lot of the data is incomplete or extreme so we tell the NAG routine
    # not to worry about warning us about data points it can't work with
    warnings.simplefilter('ignore',utils.NagAlgorithmicWarning)
    sigmaCall, ivalidCall = specfun.opt_imp_vol('C',pCall,data.Strike, s0,t,r,mode = 1)
    impvolcall = pandas.Series(sigmaCall,index=data.index, name='impvolCall')

    data = data.join(impvolcall)

    print('Calculating Implied Vol of Puts...')
    pPut= (data['Bid.1'] + data['Ask.1']) / 2
    sigmaPut, ivalidPut = specfun.opt_imp_vol('P',pPut,data.Strike, s0,t,r,mode = 1)
    impvolput = pandas.Series(sigmaPut,index=data.index, name='impvolPut')

    data = data.join(impvolput)
    fig = plt.figure(1)
    fig.subplots_adjust(hspace=.4, wspace=.3)

    # Plot the Volatility Curves
    # Encode graph layout: 3 rows, 3 columns, 1 is first graph.
    num = 331
    max_xticks = 4
    
    for date in dates:
        # add each subplot to the figure
        plot_year, plot_month = date.split()
        plot_date = (int(plot_year) - (current_year % 2000)) * 365 + cumulative_month[plot_month]
        plot_call = data[(data.impvolCall > .01) &
                       (data.Expiration == plot_date) &
                       (data['Last Sale'] > 0)]
        plot_put = data[(data.impvolPut > .01) &
                        (data.Expiration == plot_date) &
                        (data['Last Sale.1'] > 0)]

        myfig = fig.add_subplot(num)
        xloc = plt.MaxNLocator(max_xticks)
        myfig.xaxis.set_major_locator(xloc)
        myfig.set_title('Expiry: %s 20%s' % (plot_month, plot_year))
        myfig.plot(plot_call.Strike, plot_call.impvolCall, 'pr', label='call',markersize=0.5)
        myfig.plot(plot_put.Strike, plot_put.impvolPut, 'p', label='put',markersize=0.5)
        myfig.legend(loc=1, numpoints=1, prop={'size': 10})
        myfig.set_ylim([0,1])
        myfig.set_xlabel('Strike Price')
        myfig.set_ylabel('Implied Volatility')
        num += 1

    plt.suptitle('Implied Volatility for %s Current Price: %s Date: %s' %
                 (company, underlyingprice, qd_date))
    

    print("\nPlotting Volatility Curves/Surface")
    """
    The code below will plot the Volatility Surface
    It uses e02ca to fit with a polynomial and e02cb to evaluate at 
    intermediate points
    """ 

    m = np.empty(len(dates), dtype=np.int32)
    y = np.empty(len(dates), dtype=np.double)
    xmin = np.empty(len(dates), dtype=np.double)    
    xmax = np.empty(len(dates), dtype=np.double)
 
    data = data.sort_values(by=['Strike']) # Need to sort for NAG Algorithm

    k = 3   # this is the degree of polynomial for x-axis (Strike Price)
    l = 3   # this is the degree of polynomial for y-axis (Expiration Date)

    i = 0

    for date in dates:
        plot_year, plot_month = date.split()
        plot_date = (int(plot_year) - (current_year % 2000)) * 365 + cumulative_month[plot_month]
        
        call_data = data[(data.Expiration == plot_date) & 
				(data.impvolPut > .01) & 
				(data.impvolPut < 1) &
                                (data['Last Sale.1'] > 0)]
         
        exp_sizes = call_data.Expiration.size
        if(exp_sizes > 0):       
            m[i] = exp_sizes
            n = len(dates)

            if(i == 0):
                x = np.array(call_data.Strike)
                call = np.array(call_data.impvolPut)
                xmin[0] = x.min()
                xmax[0] = x.max()
            else:
                x2 = np.array(call_data.Strike)
                x = np.append(x,x2)
                call2 = np.array(call_data.impvolPut)
                call = np.append(call,call2)
                xmin[i] = x2.min()
                xmax[i] = x2.max()
            y[i] = plot_date-today
            i+=1
    nux = np.zeros(1,dtype=np.double)
    nuy = np.zeros(1,dtype=np.double)
    inux = 1
    inuy = 1

    if(len(dates) != i):
        print("Error with data: the CBOE may not be open for trading or one expiration date has null data")
        return 0
    weight = np.ones(call.size, dtype=np.double)
    
    #Call the NAG Chebyshev fitting function
    output_coef = fit.dim2_cheb_lines(m,k,l,x,y,call,weight,(k + 1) * (l + 1),xmin,xmax,nux,nuy)        
   
    """
    Now that we have fit the function,
    we use fit.dim2_cheb_eval to evaluate at different strikes/expirations 
    """

    nStrikes = 100 # number of Strikes to evaluate    
    spacing = 20 # number of Expirations to evaluate
    
    for i in range(spacing):
        mfirst = 1	
        mlast = nStrikes
        xmin = data.Strike.min()
        xmax = data.Strike.max()
         
        x = np.linspace(xmin, xmax, nStrikes)

        ymin = data.Expiration.min() - today
        ymax = data.Expiration.max() - today
      
        y = (ymin) + i * np.floor((ymax - ymin) / spacing) 

        fx=np.empty(nStrikes)

        fx=fit.dim2_cheb_eval(mfirst,k,l,x,xmin,xmax,y,ymin,ymax,output_coef)
        
        if 'xaxis' in locals():
            xaxis = np.append(xaxis, x)
            temp = np.empty(len(x))
            temp.fill(y)
            yaxis = np.append(yaxis, temp)    
            for j in range(len(x)):
                zaxis.append(fx[j])
        else:
            xaxis = x
            yaxis = np.empty(len(x), dtype=np.double)
            yaxis.fill(y)
            zaxis = []
            for j in range(len(x)):
                zaxis.append(fx[j])
   
    fig = plt.figure(2)
    ax = fig.add_subplot(111, projection='3d')

    # A try-except block for Matplotlib
    try:
        ax.plot_trisurf(xaxis, yaxis, zaxis, cmap=cm.jet)
    except AttributeError:
        print ("Your version of Matplotlib does not support plot_trisurf")
        print ("...plotting wireframe instead")
        ax.plot(xaxis, yaxis, zaxis)
    
    ax.set_xlabel('Strike Price')
    ax.set_ylabel('Days to Expiration')
    ax.set_zlabel('Implied Volatility for Put Options')
    plt.suptitle('Implied Volatility Surface for %s Current Price: %s Date: %s' %
                 (company, underlyingprice, qd_date))
    
    plt.show()    

if __name__ == "__main__":
    main()
