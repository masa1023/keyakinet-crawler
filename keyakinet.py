# coding: utf-8
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys

import dropbox

import json
import urllib.request
import requests

import schedule
import time
from datetime import datetime, timedelta, timezone
import os
import io,sys

from flask import Flask

WEBHOOK_URL = 'YOUR_SLACK_WEBHOOK_URL'

app = Flask(__name__)

@app.route('/crawlers/keyakinet')
def hello():
  JST = timezone(timedelta(hours=+9), 'JST')
  now = datetime.now(JST).strftime("%Y/%m/%d %H:%M:%S")

  print("[%s] start job" % now)


  options = Options()

  options.add_argument('--no-sandbox')
  options.add_argument('--disable-gpu')
  options.add_argument('--disable-dev-shm-usage')

  driver = webdriver.Chrome(chrome_options=options)
  driver.get('https://setagaya.keyakinet.net/Web/Home/WgR_ModeSelect')

  driver.set_window_size(1050, 1000)

  driver.get('https://setagaya.keyakinet.net/Web/Home/WgR_ModeSelect')
  driver.execute_script('document.querySelector("#tabs > ul > li.purpose").click()')
  driver.execute_script('document.querySelector("#radioPurposeLarge04").click()')
  time.sleep(2)
  driver.execute_script('document.querySelector("#checkPurposeMiddle401").click()')
  driver.execute_script('document.querySelector("#btnSearchViaPurpose").click()')
  time.sleep(2)

  driver.execute_script('document.querySelector("#nextpage > a").focus()')
  driver.find_element_by_css_selector('#nextpage > a').send_keys(Keys.ENTER)
  time.sleep(1)
  driver.execute_script('window.scrollBy(0, 300)')
  time.sleep(1)

  driver.execute_script('document.querySelector("#shisetsutbl > tr:nth-of-type(1) > .shisetsu.toggle > label").click()')
  time.sleep(1)


  driver.execute_script('document.querySelector("#shisetsutbl > tr:nth-of-type(14) > .shisetsu.toggle > label").click()')
  time.sleep(3)

  driver.execute_script('document.querySelector("#btnNext").focus()')
  driver.find_element_by_css_selector('#btnNext').send_keys(Keys.ENTER)

  driver.execute_script('window.scroll(0, 1000)')
  tds = driver.find_elements_by_css_selector('table.calendar tbody td')
  for td in tds:
    input_ele = td.find_elements_by_css_selector('input')
    label_ele = td.find_elements_by_css_selector('label')
    if len(label_ele) > 0 and (label_ele[0].text == '△' or label_ele[0].text == '○'):
      label_ele[0].click()

  time.sleep(1)
  driver.execute_script('document.querySelector(".navbar li.next > a").focus()')
  driver.find_element_by_css_selector('.navbar li.next > a').send_keys(Keys.ENTER)

  time.sleep(3)

  blocks_by_court = driver.find_elements_by_css_selector('.item_body .item.clearfix')
  results = []
  for block in blocks_by_court:
    court_name = block.find_element_by_css_selector('h3').text
    results.append('\n' + court_name)
    calendars = block.find_elements_by_css_selector('table.calendar')
    for cal in calendars:
      head_row = cal.find_element_by_css_selector('thead tr')
      body_rows = cal.find_elements_by_css_selector('tbody tr')
      date = head_row.find_element_by_css_selector('th:first-child').text
      day_of_the_week = date.split('(')[1][:1]
      results_len = len(results)

      for row in  body_rows:
        if day_of_the_week == '土' or day_of_the_week == '日':
          cells = row.find_elements_by_css_selector('td')
          for cell in cells:
            booking_condition = cell.find_element_by_css_selector('label').text
            if booking_condition == '○':
              hour = head_row.find_element_by_css_selector('th:nth-of-type(%d)' % cells.index(cell) + 1).text.replace('\n', '')
              results.append(date + hour)
        else:
          booking_condition = row.find_element_by_css_selector('td:last-child label').text
          if booking_condition == '○':
            last_hour = head_row.find_element_by_css_selector('th:last-child').text.replace('\n', '')
            results.append(date + last_hour)

  if len(results) > 0:
    split = '=============================='
    payload = {
      'text': split + '\nテニスコートの空きを発見したよ！\n' + '\n'.join(results) + '\n' + split,
      "username": "空き状況お知らせBot",
      "icon_emoji": ":tennis:",
    }
    headers = {
      'Content-Type': 'application/json',
    }

    res = requests.post(WEBHOOK_URL, data=json.dumps(payload), headers=headers)
    now = datetime.now(JST).strftime("%Y/%m/%d %H:%M:%S")
    print('[%s] %s' % (now, res))

  print('[%s] finish job' % now)
  driver.quit()

  return 'Executed keyakinet scraping'

if __name__ == '__main__':
    hello()
