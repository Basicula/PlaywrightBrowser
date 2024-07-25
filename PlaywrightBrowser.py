import json
import os
from typing import List, Any
from enum import Enum
from playwright.sync_api import sync_playwright, Page, Locator

class ContentType(Enum):
  IMAGE = "image"
  STYLE = "stylesheet"
  FONT = "font"
  XHR = "xhr"
  OTHER = "other"

class PlaywrightWebDriver:
  '''
    Basic web browser operations simulation
  '''
  def __init__(self, headless : bool = True, content_types : List[ContentType] = []) -> None:
    self.cookies_cache_path = "cookies.json"
    self.headless = headless
    self.playwright = sync_playwright().start()
    self.browser = self.playwright.firefox.launch(headless=headless)
    #self.browser = self.playwright.chromium.launch(headless=headless)
    self.context = self.browser.new_context()
    if os.path.exists(self.cookies_cache_path):
      try:
        with open(self.cookies_cache_path, "r") as fi:
          cookies = json.loads(fi.read())
          self.context.add_cookies(cookies)
      except:
        print("Can't load cookies :(")

    self.ping_page = self._new_page()
    self.pages = {0: self.ping_page}
    self.uid = 1

    self.content_types_status = {}
    for type in ContentType:
      self.content_types_status[type] = False
    for type in content_types:
      self.content_types_status[type] = True

  def stop(self) -> None:
    '''
      Close browser
    '''
    with open(self.cookies_cache_path, "w") as fo:
      json.dump(self.context.cookies(), fo)
    for page_id in self.pages:
      self.pages[page_id].close()
    self.pages.clear()
    self.context.close()
    self.browser.close()
    self.playwright.stop()

  def _new_page(self) -> Page:
    page = self.context.new_page()
    def filter_content(route, request):
      resource_type = request.resource_type
      match resource_type:
        case "image" | "stylesheet" | "other" | "xhr" | "font":
          if not self.content_types_status[ContentType(resource_type)]:
            route.abort()
          else:
            route.continue_()
        case _:
          route.continue_()

    page.route("**/*", filter_content)
    return page

  def ping(self, url : str) -> int:
    while True:
      try:
        response = self.ping_page.goto(url, wait_until='load', timeout=5000)
        return response.status
      except:
        continue

  def open(self, url : str) -> int:
    '''
      Open new tab with specific unic url
      If open failed returns -1
    '''
    new_page = self._new_page()
    if self.__goto(new_page, url) == 200:
      new_page_id = self.uid
      self.pages[new_page_id] = new_page
      self.uid += 1
      return new_page_id
    return -1

  def __goto(self, page : Page, url : str) -> int:
    while True:
      try:
        response = page.goto(url, wait_until='load', timeout=5000)
        if response.status != 200:
          page.close()
        return response.status
      except:
        continue

  def redirect(self, page_id : int, url : str) -> bool:
    '''
      Change url for tab, returns true if success, false otherwise
    '''
    try:
      if self.__goto(self.pages[page_id], url) == 200:
        return True
    except:
      print(f"Page {page_id} redirection failed")
    return False

  def close(self, page_id : int) -> None:
    '''
      Close tab
    '''
    try:
      self.pages[page_id].close()
      del self.pages[page_id]
    except:
      print(f"Closing page {page_id} failed")

  def page_content(self, page_id : int) -> str:
    '''
      Get page content
    '''
    while True:
      try:
        content = self.pages[page_id].content()
        return content
      except:
        continue

  def page_url(self, page_id : int) -> str:
    '''
      Get page url in case of something changes without any actions
    '''
    return self.pages[page_id].url

  def scroll_down(self, page_id : int) -> None:
    '''
      Scroll down simulation, 'End' button pressed
    '''
    if page_id in self.pages.keys():
      self.pages[page_id].keyboard.press('End')
      self.pages[page_id].wait_for_load_state('load')

  def scroll_up(self, page_id : int) -> None:
    '''
      Scroll up simulation, 'Home' button pressed
    '''
    if page_id in self.pages.keys():
      self.pages[page_id].keyboard.press('Home')
      self.pages[page_id].wait_for_load_state('load')

  def evaluate(self, page_id : int, script : str) -> Any:
    '''
      Run js script in console for tab
    '''
    if page_id in self.pages.keys():
      return self.pages[page_id].evaluate(script)

  def click(self, page_id : int, button_text : str) -> None:
    '''
      Click on button with given text
    '''
    if page_id in self.pages.keys():
      self.pages[page_id].locator(f"button:has-text(\"{button_text}\")").click()

  def element_by_id(self, page_id : int, element_id : str) -> Locator:
    return self.pages[page_id].locator(f"#{element_id}")
  
  def wait(self, page_id : int) -> None:
    self.pages[page_id].wait_for_load_state('load')
    