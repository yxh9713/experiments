#!/usr/bin/env python2.7

# Built for tornado 1.2

import json
import os

from tornado import auth, ioloop, web

def GET(f):
  f.GET = True
  return f

def POST(f):
  f.POST = True
  return f

class BaseHandlerException(Exception):
  pass

class BaseHandler(web.RequestHandler):
  errors = []
  flash = []

  def get_config(self):
    return self.application.vexconfig

  def prepare(self):
    self.errors = []
    self.flash = []

  def add_error(self, error):
    self.errors.append(error)

  def add_flash(self, flash):
    self.flash.append(flash)

  def get_model_api(self):
    return self.application.model_api

  def get_current_user(self):
    return self.get_secure_cookie("user")

  def set_current_user(self, user):
    self.set_secure_cookie("user", user)

  def render_ajax(self, success, data=None):
    self.set_header("Content-Type", "text/json")
    self.write(json.dumps({
      "success": success,
      "data": data,
      "errors": self.errors,
      "flash": self.flash
      }))

  def process_fail(self, message="__unset"):
    raise BaseHandlerException(
        "Error processing 'action' parameter: %s" % message)

  def process_request(self, request_type):
    action = self.get_argument("action", None)
    if not action:
      self.process_fail("Missing parameter: 'action'")
      return

    try:
      action_func = self.__getattribute__(action)
      has_handler = action_func.__getattribute__(request_type)
    except Exception, e:
      self.process_fail(e)
      return

    if (has_handler):
      action_func()
    else:
      self.process_fail("Missing handler for: " + action)

  def get(self):
    return self.process_request("GET")

  def post(self):
    return self.process_request("POST")

  def render_template(self, path, **kwargs):
    return self.render(path,
                       errors=self.errors,
                       flash=self.flash,
                       **kwargs)


class GoogleLoginHandler(BaseHandler, auth.GoogleMixin):
  @web.asynchronous
  def get(self):
    if self.get_argument("openid.mode", None):
      self.get_authenticated_user(self.async_callback(self._on_auth))
      return

    self.authenticate_redirect()

  def _on_auth(self, user):
    if not user:
      logging.error("Login failed")
      self.authenticate_redirect()
      return

    self.set_current_user(user["email"])
    self.redirect("/")
