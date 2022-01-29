import requests
import json
import re

BASE_URL = "https://cbet.gg/br"
URL_API = "https://cbet.gg/api"
SERVER_URL = "https://eu-server-w2.ssgportal.com"


class Browser(object):

    def __init__(self):
        self.response = None
        self.headers = self.get_headers()
        self.session = requests.Session()

    def get_headers(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/87.0.4280.88 Safari/537.36"
        }
        return self.headers

    def send_request(self, method, url, **kwargs):
        response = self.session.request(method, url, **kwargs)
        if response.status_code in [401, 200]:
            return response
        return None


class CbetAPI(Browser):

    def __init__(self, username, password):
        super().__init__()
        self.token = None
        self.referer = None
        self.username = username
        self.password = password
        self.auth()

    def auth(self):
        data = {
            "username": self.username,
            "password": self.password
        }
        self.response = self.send_request("POST",
                                          URL_API + "/profile/login",
                                          json=data,
                                          headers=self.headers)
        return self.response

    def get_user_status(self):
        self.response = self.send_request("GET",
                                          f"{URL_API}/profile/p/getuserauthstatus",
                                          headers=self.headers)
        return self.response.json()

    def get_profile(self):
        self.response = self.send_request("GET",
                                          f"{URL_API}/profile/p/getprofile",
                                          headers=self.headers)
        return self.response.json()

    def get_game_launcher(self):
        data = {
            "GameTemplateId": 10615,
            "CurrencyId": 174,
            "Language": 34,
            "IsReal": True,
            "GameLaunchParam": 1
        }
        self.response = self.send_request("GET",
                                          f"{URL_API}/game/getgametemplateplayurl",
                                          params=data,
                                          headers=self.headers)
        self.load_player()

    def load_player(self):
        self.response = self.send_request("GET",
                                          self.response.json()["response"]["DesktopUrl"],
                                          headers=self.headers)

        self.token = re.findall(r'input .*? value="(.*?)" id="HiddenTokenKey"', self.response.text)[0]
        self.get_loader()

    def get_loader(self):
        data = {
            "Gametype": "",
            "GameName": "JetX",
            "StartPage": "Board",
            "Token": self.token,
            "Lang": "en",
            "ReturnUrl": "https://CBET5.GG",
            "StopUrl": ""
        }
        self.response = self.send_request("GET",
                                          f"{SERVER_URL}/JetXNode31/JetX/Loader.aspx",
                                          params=data,
                                          headers=self.headers)
        self.player_start()

    def player_start(self):
        self.headers["referer"] = f"{SERVER_URL}/JetXNode3/JetX/Board.aspx?" \
                                  f"Token={self.token}&ReturnUrl=https%3a%2f%2fCBET5.GG&StopUrl="
        self.response = self.send_request("GET",
                                          f"{SERVER_URL}/JetXNode31//api/JetXapi/Player/{self.token}",
                                          headers=self.headers)

    def get_data(self):
        self.get_game_launcher()
        self.headers["referer"] = f"{SERVER_URL}/JetXNode3/JetX/Board.aspx?" \
                                  f"Token={self.token}&ReturnUrl=https%3a%2f%2fCBET5.GG&StopUrl="
        self.response = self.send_request("GET",
                                          f"{SERVER_URL}/JetXNode31//api/JetXapi/Board/{self.token}",
                                          headers=self.headers)
        return self.response.json()


if __name__ == '__main__':
    cba = CbetAPI("user", "password")
    if cba.get_user_status()["auth"]:
        result = {"items": [{"color": "vermelho" if i["Coefficient"] < 1.5 else "verde", "value": i["Coefficient"]}
                            for i in cba.get_data()["Last100Spins"]]}
        print(json.dumps(result, indent=4))
