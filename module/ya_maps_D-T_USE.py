from selenium import webdriver
from selenium.webdriver.common.proxy import *
import time


class YandexMapParser:
    def __init__(self,*, width, height, proxy):
        header_size = 74
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        PROXY = proxy #'195.208.172.70:8080'# '37.230.114.6:3128'

        prox = Proxy()
        prox.proxy_type = ProxyType.MANUAL
        prox.http_proxy = PROXY
        prox.socks_proxy = PROXY
        prox.ssl_proxy = PROXY

        capabilities = webdriver.DesiredCapabilities.CHROME
        prox.add_to_capabilities(capabilities)

        try:
            self.browser = webdriver.Chrome(executable_path='C:\\Users\\Vadim\\chrome_driver\\chromedriver.exe',
                                        desired_capabilities=capabilities, options=options)
            self.browser.set_window_size(width, height + header_size)
        except Exception:
            print('Browser dont init', Exception)



    def change_window_size(self, width, height):
        self.browser.set_window_size(width, height)

    def screenshot(self, *, url=None, lat=None, lon=None, z=None, sleep_time=10):
        if url is None:
            url = 'https://yandex.ru/maps/?clid=1929744&ll={}%2C{}&z={}&l=sat'.format(lon, lat, z)
            #url = 'https://yandex.ru/maps/?l=sat&ll={}%2C{}&z={}'.format(lon, lat, z)
        try:
            self.browser.get(url)
        except:
            return None
        time.sleep(sleep_time)
        if 'google' in url and url.startswith('http'):
            js_code = """
                //document.getElementsByClassName('searchbox-hamburger')[0].click();
                window.setTimeout(clicker, 6000);
                //remover();
                
                function clicker() {
                    document.getElementsByClassName('widget-settings-button').click();
                    document.getElementsByClassName('section-homescreen-header').click();
                    var checkZoom = document.getElementsByClassName('widget-tilt-button-text')[0].innerText;
                    if (checkZoom == '2D'){
                        document.getElementsByClassName('widget-tilt-button')[0].click();
                    }
                    window.setTimeout(remover, 6000);
                }

                function remover() {
                    document.getElementById('omnibox').remove();
                    document.getElementById('omnibox-container').remove();
                    document.getElementById('vasquette').remove();
                }
                function pause(ms){
                    var d = new Date();
                    var d2 = null;
                    do { d2 = new Date(); }
                    while(d2-d < ms);
                }
            """
        elif 'yandex' in url and url.startswith('http'):
            js_code = """
                document.getElementById('sidebar-container').remove();
                document.getElementById('map-controls').remove();
                document.getElementsByClassName('header').remove();
                document.getElementsByClassName('ymaps-2-1-64-copyrights-pane').remove();
                
            """
            #document.getElementsByClassName('branding-control _noprint')[0].remove();
            #ym_cls = 'ymaps-2-1-64-copyright ymaps-2-1-64-copyright_color_white ymaps-2-1-64-copyright_logo_no';
            #// document.getElementsByClassName(ym_cls)[0].remove();
        else:
            return None
        try:
            self.browser.execute_script(js_code)
            time.sleep(sleep_time)
        except Exception:
            print('JS code fail')

        return self.browser.get_screenshot_as_png()

    def __del__(self):
        self.browser.quit()
