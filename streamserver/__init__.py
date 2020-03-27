#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from apppath import AppPath

__project__ = "StreamServer"
__author__ = "Soeren Rasmussen"
__version__ = "0.4.2"
__doc__ = r"""
          .. module:: streamserver
             :platform: Unix, Windows
             :synopsis: multipart image HTTP streaming server.

          .. moduleauthor:: Soeren Rasmussen

          Created on 27/04/2018

          @author: Soeren Rasmussen
          """

PROJECT_NAME = __project__.lower().strip().replace(" ", "_")
PROJECT_AUTHOR = __author__.lower().strip().replace(" ", "_")
PROJECT_APP_PATH = AppPath(app_name=PROJECT_NAME, app_author=PROJECT_AUTHOR)
