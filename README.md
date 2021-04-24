# Implied Volatility Using Python's Pandas Package

This code is to accompany the corresponding Numerical Algorithms Group (NAG) blog post.

> https://www.nag.com/content/implied-volatility-using-pythons-pandas-library (which has been updated in 2021 to use the NAG Library for Python)

This script uses options data downloaded from the [CBOE] in csv format. Be sure to download data during CBOE trading hours to ensure the graphs are not null. To run type
```sh
$ python implied_volatility.py QuoteData.dat
```

This script has been tested with the following packages:

  - Python 3.8
  - numpy 1.16.4
  - pandas 0.24.2
  - matplotlib 3.1.0
  - NAG Library for Python, Mark 27.1

A [NAG Library for Python] license is required to run the script. To obtain a free 30-day trial license, email support@nag.co.uk

![Alt text](/pictures/VolatilityCurves.png?raw=true "Volatility Curves for AAPL")
![Alt text](/pictures/VolatilitySurface.png?raw=true "Volatility Surface for AAPL")

[NAG Library for Python]: https://www.nag.com/content/nag-library-python
[CBOE]: http://www.cboe.com/delayedquote/QuoteTableDownload.aspx
