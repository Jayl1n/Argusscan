# Argusscan 分布式SQL注入检测系统

# 简介

使用`Python`开发，`客户端`通过`scapy`采集本机的HTTP流量，转发到`服务器`，由`服务器`对漏洞检测任务进行统一管理，分配给`Slave节点`执行。

# Client

客户端，在`setting.ini`中进行HTTP流量采集和服务器地址的相关配置后，运行`client.py`即可。

# Master

服务器端，使用`sqlite`作为数据库，免去了繁琐的服务器配置。提供WEB操控界面，在`setting.ini`中可以配置WEB监听的地址和端口，配置完成后，运行`master.py`启动。

# Slave

Slave节点端，基于`sqlmap`，负责执行SQL注入检测任务。在`setting.ini`中，配置好`Master`相关信息及`Slave`运行的端口后，运行`slave.py`启动。
