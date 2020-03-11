# Data App Project (Prescient Finance)
A Web Application that allows users to create dummy portfolios or watchlists to monitor or test their trading strategies. Written in Python using the Flask web framework.
Front-End: HTML, CSS, JS
Back-End: Flask(Python), SQL-Alchemy
Other Libraries: Pandas

image 1 - login page
image 2 - dashboard

# Table of Contents
- [Introduction](https://github.com/RamonWill/Data-App#Introduction)
- [Features](https://github.com/RamonWill/Data-App#Features)
- [How it Works](https://github.com/RamonWill/Data-App#Installation)
- [Credits](https://github.com/RamonWill/Data-App#Credit)
- [Video Demo](https://github.com/RamonWill/Data-App#Video-Demo)
- [Screenshots](https://github.com/RamonWill/Data-App#Screenshots)

# Introduction
Prescient Finance allows users to create an unlimited number of portfolios/watchlists to test out their strategies, monitor potential performance, or to simply track certain sectors. Users have a choice of over 1500+ equities from 10 different markets.

# Features
Prescient Finance allows users to:
* Time-series Performance charts at both a portfolio and individual stock level
* View daily unrealised P&L breakdowns of their positions
* Perform CRUD operations on their portfolios
* View the daily Holding Period Return on a portfolio
* Statistical graphics to help visualise portfolio exposure.

# How it Works
A user registers to the site, logins in and then creates a portfolio. Next the user can add securities to the portfolio and enter trade details and economics. The site will then display the various features based on the information entered by the user. If the security does not yet have a prices stored in the database. An api call will be made instantly to Alpha Vantage and the most recent 100 EOD prices will be stored to the database. // I will make a feature at some point to automatically update prices at EOD. 

# Credits
A big thank you to the Flask community for designing an interesting and flexible FrameWork. I would also like to thank Alpha Vantage again for the easy access to a wide range of financial data.

* Disclaimer: This project is not valid financial tool. It is a project that I've created to help me learn more about Python. You should in no way use it to make investment decisions.

# Video-Demo
Coming Soon

# Screenshots
Coming Soon
