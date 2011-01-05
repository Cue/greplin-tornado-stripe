#  Copyright 2010 Greplin, Inc. All Rights Reserved.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http:#www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS-IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

# Author: Daniel Gross <daniel@greplin.com>
# Based on the python bindings by Patrick Collison <patrick@collison.ie>

"""
Asynchronous Tornado bindings for the devpayments API
"""

import functools
import urllib

try:
  from tornado import httpclient, escape
except ImportError:
  raise ImportError("Tornado is required for this binding. See http://www.tornadoweb.org/ for more information")



class Client(object):
  """A client for devpayment's API for use with Tornado
  Usage (within a RequestHandler):

    def post(self):
      devpay = devpayments.Client(self.settings['devpayments_secret'])
      sample_card = {
        'number': '4242424242424242',
        'exp_month': 10,
        'exp_year': 2011
      }
      devpay.execute(self.async_callback(self._on_executed),
                     amount=2000, currency='usd', card=sample_card,
                     mnemonic='customer@gmail.com')



    def _on_executed(self, res, context):
      self.write(res.id)
      self.finish()

  """
  API_URL = "https://api.devpayments.com/v1"


  def __init__(self, key, raise_errors=True):
    self._key = key
    self._raise_errors = raise_errors


  def retrieve(self, callback, **params):
    """
    Fetch a DP charge token representing the supplied transaction as described in params,
    assuming the transaction has previously been prepared or executed; does not execute the transaction.
    """
    self._require(params, ['id'])
    self._call(callback, 'retrieve_charge', params)


  def execute(self, callback, **params):
    """
    Execute the described transaction. Transaction is specified either using a DP token or by supplying amount and currency arguments.

      params:
        {
        * amount: integer amount to be charged in cents
        * currency: lowercase 3-character string from set {usd, cad, ars,...} - for full specification see http://en.wikipedia.org/wiki/ISO_4217
        }
        AND
        * card: dictionary object describing card details
        {
          * number: string representing credit card number
          * exp_year: integer representing credit card expiry year
          * exp_month: integer representing credit card expiry month
          *OPTIONAL* name: string representing cardholder name
          *OPTIONAL* address_line_1: string representing cardholder address, line 1
          *OPTIONAL* address_line_2: string representing cardholder address, line 2
          *OPTIONAL* address_zip: string representing cardholder zip
          *OPTIONAL* address_state: string representing cardholder state
          *OPTIONAL* address_country: string representing cardholder country
          *OPTIONAL* cvc: CVC Number
        }
        OR
        * customer: the id of an existing customer

    """
    self._require(params, ['amount', 'currency'])
    self._call(callback, 'execute_charge', params)


  def refund(self, callback, **params):
    """
    Refund a previously executed charge by passing this method the charge token
    """
    self._require(params, ['id'])
    self._call(callback, 'refund_charge', params)


  def create_customer(self, callback, **params):
    """
    Create a new customer with the given token, and set the supplied
    credit card as the active card to be their active card.
    Used for recurring billing.
    """
    return self._call(callback, 'create_customer', params)


  def update_customer(self, callback, **params):
    """
    Set a credit card as the active card for a given customer. Used for recurring billing.
    """
    self._require(params, ['id'])
    return self._call(callback, 'update_customer', params)


  def bill_customer(self, callback, **params):
    """
    Add a once-off amount to a customer's account. Used for recurring billing.
    """
    self._require(params, ['id', 'amount'])
    return self._call(callback, 'bill_customer', params)


  def retrieve_customer(self, callback, **params):
    """
    Retrieve billing info for the given customer. Used for recurring billing.
    """
    self._require(params, ['id'])
    return self._call(callback, 'retrieve_customer', params)


  def delete_customer(self, callback, **params):
    """
    Delete the given customer. They will not be charged again, even if their is an outstanding balance on their account.
    """
    self._require(params, ['id'])
    return self._call(callback, 'delete_customer', params)


  def _nested_dict_to_url(self, d):
    """
    We want post vars of form:
    {'foo': 'bar', 'nested': {'a': 'b', 'c': 'd'}}
    to become (pre url-encoding):
    foo=bar&nested[a]=b&nested[c]=d
    """
    stk = []
    for key, value in d.items():
      if isinstance(value, dict):
        n = {}
        for k, v in value.items():
          n["%s[%s]" % (key, k)] = v
        stk.extend(self._nested_dict_to_url(n))
      else:
        stk.append((key, value))
    return stk


  def _require(self, params, req):
    """
    Internal: strict verification of parameter list
    """
    for r in req:
      if r not in params:
        raise InvalidRequestException("Missing required param: %s" % r)


  def _call(self, callback, method, extra_params):
    """
    Internal: Call a devpaymnets API method
    """
    params = {
      'method':method,
      'key':self._key,
      'client':{'type':'binding', 'language':'python_tornado', 'version':'1.4.3'}
    }
    if extra_params:
      params.update(extra_params)
    http = httpclient.AsyncHTTPClient()
    http.fetch(self.API_URL, functools.partial(self._parse_response, callback, method),
               method="POST", body=urllib.urlencode(self._nested_dict_to_url(params)))


  def _parse_response(self, callback, method, response):
    """Parse a response from the API"""
    res = escape.json_decode(response.body)
    if res.get('error'):
      err = {
        'card_error': CardException,
        'invalid_request_error': InvalidRequestException,
        'api_error': APIException
      }
      if self._raise_errors:
        raise err[res['error']['type']](res['error']['message'])
    callback(Response(res), method)



class Response(object):
  """A Devpayments response object"""


  def __init__(self, res_dict):
    self._dict = res_dict


  def __getattr__(self, name):
    return self._dict[name]


  def __dict__(self):
    return self._dict



class DevPayException(Exception):
  """Generic exception class for all Devpayments errors"""


  def __init__(self, msg):
    super(DevPayException, self).__init__(msg)



class APIConnectionError(DevPayException):
  pass



class CardException(DevPayException):
  pass



class InvalidRequestException(DevPayException):
  pass



class APIException(DevPayException):
  pass
