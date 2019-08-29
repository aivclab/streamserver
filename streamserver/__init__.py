#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from apppath import AppPath

from .streamserver import StreamServer

__all__ = ["StreamServer"]


__author__ = "cnheider"
__version__ = "0.3.2"
__doc__ = r"""
          .. module:: streamserver
             :platform: Unix, Windows
             :synopsis: multipart image HTTP streaming server.
          
          .. moduleauthor:: Christian Heider Nielsen <christian.heider@alexandra.dk>
          
          Created on 27/04/2019
          
          @author: cnheider
          """


PROJECT_NAME = "StreamServer"
PROJECT_AUTHOR = __author__
PROJECT_APP_PATH = AppPath(app_name=PROJECT_NAME, app_author=PROJECT_AUTHOR)
