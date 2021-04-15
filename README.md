# advanced-python-made-2020
MADE Advanced Python Course

This repository contains 3 homework for the Advanced Python course.

* Create environment:
```bash
export env_name="advanced-python"
conda create -n $env_name python=3.7
conda activate $env_name
conda install --file requirements.txt
```
## Table of content

- [Inverted Index Module](#Inverted Index Module)
- [StackOverflow Analytics](#StackOverflow Analytics)
- [Asset Web Service](#Asset Web Service)


## Inverted Index Module
This module is designed to work with Inverted Index.
This module is based on the class Inverted index. It contains the logic of inverted 
index work.
it allows you to load from a file, save, and query the inverted index.

## StackOverflow Analytics
Stackoverflow post analytics app. 
The application provides a console interface for answering questions about 
the most popular discussion topics for a specified period (years).

## Asset Web Service

Financial and analytical Web Service, which
will allow you to monitor changes in the exchange rate and their impact on investment
products. To solve the task, you will need the following skills:
* parse HTML (for example, using bs4, lxml and / or XPath);
* use design patterns (eg Composite);
* test and raise Python web services with Flask and pytest;
* write and organize Jinja2 templates;
* log, monitor and launch a Web service on the PaaS platform.