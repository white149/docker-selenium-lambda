from selenium import webdriver
from tempfile import mkdtemp
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
import psycopg2
import json
import requests
import time
import io
import pickle


class Browser:
    def __init__(self, login_info) -> None:
        self.username = login_info["username"]
        self.password = login_info["password"]
        options = webdriver.ChromeOptions()
        options.binary_location = "/opt/chrome/chrome"
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1280x1696")
        options.add_argument("--single-process")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-dev-tools")
        options.add_argument("--no-zygote")
        options.add_argument(f"--user-data-dir={mkdtemp()}")
        options.add_argument(f"--data-path={mkdtemp()}")
        options.add_argument(f"--disk-cache-dir={mkdtemp()}")
        options.add_argument("--remote-debugging-port=9222")
        self.s_session = webdriver.Chrome("/opt/chromedriver", options=options)
        self.session = requests.Session()
        # self.db = DBOperation()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.3 Mobile/15E148 Safari/604.1"
            }
        )

    def _fg_login(self):

        self._fg_save_cookie()
        self._fg_load_cookies_to_session()

        # self.cookie_binary = self.db.get_cookie()
        # self._fg_load_cookies_to_session()
        ss = self.session.get(
            "https://mobile.fashiongo.net/api/mobile/myAccount/order?pn=1&ps=20&orderBy=CheckoutDateDesc&"
        ).text
        self.check_data = json.loads(ss)["data"]
        # print(ss)
        # return {"status": 200, "body": ss}

        # r = json.loads(
        #     self.session.get("https://mobile.fashiongo.net/api/mobile/myAccount/").text
        # )["data"]
        # print(r)

    def _fg_save_cookie(self, quit=True):

        elements = [
            "input[formcontrolname='userName']",
            "input[formcontrolname='password']",
            "button[data-nclick-name='site.top.login']",
        ]

        login_url = "https://mobile.fashiongo.net/#/login?returnUrl=/account"
        self.s_session.get(login_url)
        actions = ActionChains(self.s_session)
        actions.pause(1)

        for i, selector in enumerate(elements):
            element = self.s_session.find_element(by=By.CSS_SELECTOR, value=selector)
            actions.move_to_element(element)
            actions.click(on_element=element)
            actions.pause(1)
            if i == 0:
                actions.send_keys(self.username)
            elif i == 1:
                actions.send_keys(self.password)
        actions.perform()
        time.sleep(2)
        in_mem_file = io.BytesIO()
        pickle.dump(self.s_session.get_cookies(), in_mem_file)
        in_mem_file.seek(0)

        self.cookie_binary = in_mem_file.read()
        self._fg_load_cookies_to_session()
        # self.db.update_cookie(self.cookie_binary)
        # if self.is_mobile:
        #     BuyerProp.objects.filter(id=b_prop_obj.id).update(
        #         mcookie=in_mem_file.read(), mcookie_update=timezone.now()
        #     )
        # else:
        #     BuyerProp.objects.filter(id=b_prop_obj.id).update(
        #         cookie=in_mem_file.read(), cookie_update=timezone.now()
        #     )
        # self.s_session.delete_all_cookies()
        if quit:
            self.s_session.quit()

    def fg_login_and_return_cookies(self):
        try:
            self._fg_login()
            return {"cookies": self.cookies, "checkData": self.check_data}
        except Exception as e:
            print(e)
            return {"status": 500, "body": "error"}

    def _fg_load_cookies_to_session(self):
        # self.buyer_prop = BuyerProp.objects.get(buyer=self.buyer)
        # cookies_binary = (
        #     self.buyer_prop.mcookie if self.is_mobile else self.buyer_prop.cookie
        # )
        self.cookies = pickle.load(io.BytesIO(self.cookie_binary))
        for cookie in self.cookies:
            self.session.cookies.set(cookie["name"], cookie["value"])

            if cookie["name"] == "MO_SSO_SESSION":
                auth_content = "Bearer " + cookie["value"]
                self.session.headers.update({"Authorization": auth_content})
            elif cookie["name"] == "NNB":
                self.session.headers.update({"NNB": cookie["value"]})
        self.session.headers.update({"OS-TYPE": "web"})


class DBOperation:
    def __init__(self) -> None:
        self.conn = psycopg2.connect(
            host="test-free.cxjzfmnjlwbd.us-west-2.rds.amazonaws.com",
            database="pitts",
            user="pitts",
            password="3QrqnbPGWp3DVQ",
        )
        self.cursor = self.conn.cursor()

    def update_cookie(self, pickle_binary):
        sql_update_query = """Update newtable set cookie = %s where id = 2"""
        # query = """select * from newtable where id = 2"""
        self.cursor.execute(sql_update_query, (pickle_binary,))
        self.conn.commit()
        return

    def get_cookie(self):
        sql_update_query = """select cookie from newtable where id = 2"""
        self.cursor.execute(sql_update_query)
        return self.cursor.fetchone()[0]


def handler(event=None, context=None):
    login_info = json.loads(event["body"])
    # nessary for lambda, otherwise it shows key error
    browser = Browser(login_info)
    return browser.fg_login_and_return_cookies()
