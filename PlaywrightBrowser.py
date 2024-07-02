from typing import List, Any
from enum import Enum
from playwright.sync_api import sync_playwright, Page

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
    self.headless = headless
    self.playwright = sync_playwright().start()
    self.browser = self.playwright.firefox.launch(headless=headless)
    self.context = self.browser.new_context()

    self.ping_page = self._new_page()
    self.pages = {}

    self.content_types_status = {}
    for type in ContentType:
      self.content_types_status[type] = False
    for type in content_types:
      self.content_types_status[type] = True

  def stop(self) -> None:
    '''
      Close browser
    '''
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
    '''
    if not url in self.pages.keys():
      self.pages[url] = self._new_page()
    while True:
      try:
        response = self.pages[url].goto(url, wait_until='load', timeout=5000)
        if response.status != 200:
          self.close(url)
        return response.status
      except:
        continue

  def redirect(self, old_url : str, new_url : str) -> int:
    '''
      Change url for tab
    '''
    self.close(old_url)
    return self.open(new_url)

  def close(self, url : str) -> None:
    '''
      Close tab
    '''
    if url in self.pages.keys():
      self.pages[url].close()
      del self.pages[url]

  def page_content(self, url : str) -> str:
    '''
      Get page content
    '''
    while True:
      try:
        content = self.pages[url].content()
        return content
      except:
        continue

  def page(self, url : str) -> Page:
    '''
      Get tab as object
    '''
    if url in self.pages.keys():
      return self.pages[url]
    return None

  def scroll_down(self, url : str) -> None:
    '''
      Scroll down simulation, 'End' button pressed
    '''
    if url in self.pages.keys():
      self.pages[url].keyboard.press('End')

  def scroll_up(self, url : str) -> None:
    '''
      Scroll up simulation, 'Home' button pressed
    '''
    if url in self.pages.keys():
      self.pages[url].keyboard.press('Home')

  def evaluate(self, url : str, script : str) -> Any:
    '''
      Run js script in console for tab
    '''
    return self.pages[url].evaluate(script)
  
  def click(self, url : str, button_text : str) -> None:
    '''
      Click on button with given text
    '''
    self.pages[url].locator(f"button:has-text(\"{button_text}\")").click()