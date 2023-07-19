import time
import random
import datetime
import requests
from sys import exit
from threading import Thread
from streamlink import Streamlink
from fake_useragent import UserAgent


class ViewerBot:
    def __init__(self, nb_of_threads, channel_name, proxylist, proxy_imported, timeout, stop=False, type_of_proxy="http"):
        self.nb_of_threads = nb_of_threads
        self.nb_requests = 0
        self.stop_event = stop
        self.proxylist = proxylist
        self.all_proxies = []
        self.proxyrefreshed = True
        try:
            self.type_of_proxy = type_of_proxy.get()
        except:
            self.type_of_proxy = type_of_proxy
        self.proxy_imported = proxy_imported
        self.timeout = timeout
        self.channel_url = "https://www.twitch.tv/" + channel_name
        self.proxyreturned1time = False 

    def create_session(self):
        # Create a session for making requests
        self.ua = UserAgent(use_external_data=True)
        self.session = Streamlink()
        self.session.set_option("http-headers", {
            "Accept-Language": "en-US,en;q=0.5",
            "Connection": "keep-alive",
            "DNT": "1",
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": self.ua.random,
            "Client-ID": "ewvlchtxgqq88ru9gmfp1gmyt6h2b93",
            "Referer": "https://www.google.com/"
        })
        return self.session

    def get_proxies(self):
        # Fetch proxies from an API or use the provided proxy list
        if self.proxylist == None or self.proxyrefreshed == False: 
            try:
                response = requests.get(f"https://api.proxyscrape.com/v2/?request=displayproxies&protocol={self.type_of_proxy}&timeout={self.timeout}&country=all&ssl=all&anonymity=all")
                if response.status_code == 200:
                    lines = []
                    lines = response.text.split("\n")
                    lines = [line.strip() for line in lines if line.strip()]
                    self.proxyrefreshed = True
                    return lines
            except:
                pass
        elif self.proxyreturned1time == False:
            self.proxyreturned1time = True
            return self.proxylist

    def get_url(self):
        # Retrieve the URL for the channel's stream
        try:
            streams = self.session.streams(self.channel_url)
            try:
                url = streams['audio_only'].url
            except:
                url = streams['worst'].url
        except:
            pass
        try: 
            return url
        except:
            exit()

    def open_url(self, proxy_data):
        # Open the stream URL using the given proxy
        headers = {'User-Agent': self.ua.random}
        current_index = self.all_proxies.index(proxy_data)

        if proxy_data['url'] == "":
            # If the URL is not fetched for the current proxy, fetch it
            proxy_data['url'] = self.get_url()
        current_url = proxy_data['url']
        username = proxy_data.get('username')
        password = proxy_data.get('password')
        if username and password:
            # Set the proxy with authentication if username and password are available
            current_proxy = {"http": f"{username}:{password}@{proxy_data['proxy']}", "https": f"{username}:{password}@{proxy_data['proxy']}"}
        else:
            current_proxy = {"http": proxy_data['proxy'], "https": proxy_data['proxy']}

        try:
            if time.time() - proxy_data['time'] >= random.randint(1, 5):
                # Refresh the proxy after a random interval
                current_proxy = {"http": proxy_data['proxy'], "https": proxy_data['proxy']}
                with requests.Session() as s:
                    response = s.head(current_url, proxies=current_proxy, headers=headers, timeout=(self.timeout/1000))
                self.nb_requests += 1
                proxy_data['time'] = time.time()
                self.all_proxies[current_index] = proxy_data
        except:
            pass

    def stop(self):
        # Stop the ViewerBot by setting the stop event
        self.stop_event = True

    def main(self):

        proxies = self.get_proxies()
        start = datetime.datetime.now()
        self.create_session()
        while not self.stop_event:
            elapsed_seconds = (datetime.datetime.now() - start).total_seconds()

            for p in proxies:
                # Add each proxy to the all_proxies list
                self.all_proxies.append({'proxy': p, 'time': time.time(), 'url': ""})

            for i in range(0, int(self.nb_of_threads)):
                # Open the URL using a random proxy from the all_proxies list
                self.threaded = Thread(target=self.open_url, args=(self.all_proxies[random.randrange(len(self.all_proxies))],))
                self.threaded.daemon = True  # This thread dies when the main thread (only non-daemon thread) exits.
                self.threaded.start()

            if elapsed_seconds >= 300 and not self.proxy_imported:
                # Refresh the proxies after 300 seconds (5 minutes)
                start = datetime.datetime.now()
                proxies = self.get_proxies()
                elapsed_seconds = 0  # Reset elapsed time
                self.proxyrefreshed = False