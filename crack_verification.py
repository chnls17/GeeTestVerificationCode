import time
from io import BytesIO
from PIL import Image
from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import settings


class CrackGeetest():
    def __init__(self):
        self.url = settings.URL
        self.chrome_options = webdriver.ChromeOptions()
        self.chrome_options.add_argument("user-agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.75 Safari/537.36'")
        self.browser = webdriver.Chrome(chrome_options=self.chrome_options)
        self.wait = WebDriverWait(self.browser, 20)
        self.email = settings.USER["USERNAME_OR_EMAIL"] or ""
        self.password = settings.USER["PASSWORD"] or ""

    def __del__(self):
        self.browser.close()

    def get_verify_button(self):
        """
        获取初始验证按钮
        :return:
        """
        button = None
        if settings.INITIAL_VALIDATION_ATTRIBUTE:
            button = self.wait.until(EC.element_to_be_clickable(
                (By.CLASS_NAME, settings.INITIAL_VALIDATION_ATTRIBUTE)))
        if button:
            return button
        else:
            return None

    def get_position(self):
        """
        获取验证码位置
        :return: 验证码位置元组
        """
        img = self.wait.until(EC.presence_of_element_located(
            (By.CLASS_NAME, settings.LOCATION_ATTRIBUTE_BY_CLASS)))
        time.sleep(2)
        if img:
            location = img.location
            size = img.size
        else:
            img = self.wait.until(EC.presence_of_element_located(
                (By.ID, settings.LOCATION_ATTRIBUTE_BY_ID)))
            location = img.location
            size = img.size
        top, bottom, left, right = location['y'], location['y'] + size[
            'height'], location['x'], location['x'] + size[
                                       'width']
        return top, bottom, left, right

    def get_screenshot(self):
        """
        获取网页截图
        :return: 截图对象
        """
        screenshot = self.browser.get_screenshot_as_png()
        screenshot = Image.open(BytesIO(screenshot))
        return screenshot

    def get_slider(self):
        """
        获取滑块
        :return: 滑块对象
        """
        slider = self.wait.until(EC.element_to_be_clickable(
            (By.CLASS_NAME, settings.SLIDER_BUTTON_BY_CLASS)))
        if slider:
            return slider
        else:
            slider = self.wait.until(
                EC.element_to_be_clickable(
                    (By.ID, settings.SLIDER_BUTTON_BY_ID)))
            return slider

    def get_verify_image(self, name=None):
        """
        获取验证码图片
        :return: 图片对象
        """
        top, bottom, left, right = self.get_position()
        print('验证码位置', top, bottom, left, right)
        screenshot = self.get_screenshot()
        captcha = screenshot.crop((left, top, right, bottom))
        # captcha.save(name)
        return captcha

    def open(self):
        """
        打开网页输入用户名密码
        :return: None
        """
        try:
            self.browser.get(self.url)
            username_or_email = self.wait.until(EC.presence_of_element_located(
                (By.ID, settings.USERNAME_OR_EMAIL_BY_ID)))
            password = self.wait.until(EC.presence_of_element_located(
                (By.ID, settings.PASSWORD_BY_ID)))
            if username_or_email and password:
                username_or_email.send_keys(self.email)
                password.send_keys(self.password)
            else:
                username_or_email = self.wait.until(
                    EC.presence_of_element_located(
                        (By.CLASS_NAME, settings.USERNAME_OR_EMAIL_BY_ID)))
                password = self.wait.until(
                    EC.presence_of_element_located(
                        (By.CLASS_NAME, settings.PASSWORD_BY_CLASS)))
                username_or_email.send_keys(self.email)
                password.send_keys(self.password)
        except Exception as e:
            print(e)
            return " The url is not correct!"

    def get_gap(self, image1, image2):
        """
        获取缺口偏移量
        :param image1: 不带缺口图片
        :param image2: 带缺口图片
        :return:
        """
        left = 60
        for i in range(left, image1.size[0]):
            for j in range(image1.size[1]):
                if not self.is_pixel_equal(image1, image2, i, j):
                    left = i
                    return left
        return left

    def is_pixel_equal(self, image1, image2, x, y):
        """
        判断两个像素是否相同
        :param image1: 图片1
        :param image2: 图片2
        :param x: 位置x
        :param y: 位置y
        :return: 像素是否相同
        """
        # 取两个图片的像素点
        pixel1 = image1.load()[x, y]
        pixel2 = image2.load()[x, y]
        threshold = 60
        if abs(pixel1[0] - pixel2[0]) < threshold and abs(
                pixel1[1] - pixel2[1]) < threshold and abs(
            pixel1[2] - pixel2[2]) < threshold:
            return True
        else:
            return False

    def get_track(self, distance):
        """
        根据偏移量获取移动轨迹
        :param distance: 偏移量
        :return: 移动轨迹
        """
        # 移动轨迹
        track = []
        # 当前位移
        current = 0
        # 减速阈值
        mid = distance * 4 / 5
        # 计算间隔
        t = 0.3
        # 初速度
        v = 0

        while current < distance:
            if current < mid:
                # 加速度为正2
                a = 3
            else:
                # 加速度为负3
                a = -3
            # 初速度v0
            v0 = v
            # 当前速度v = v0 + at
            v = v0 + a * t
            # 移动距离x = v0t + 1/2 * a * t^2
            move = v0 * t + 1 / 2 * a * t * t
            # 当前位移
            current += move
            # 加入轨迹
            track.append(round(move))
        return track

    def move_to_gap(self, slider, track):
        """
        拖动滑块到缺口处
        :param slider: 滑块
        :param track: 轨迹
        :return:
        """
        ActionChains(self.browser).click_and_hold(slider).perform()
        for x in track:
            ActionChains(self.browser).move_by_offset(xoffset=x,
                                                      yoffset=0).perform()
        time.sleep(0.5)
        ActionChains(self.browser).release().perform()

    def login(self):
        """
        登录
        :return:
        """
        submit = self.wait.until(EC.element_to_be_clickable(
            (By.CLASS_NAME, settings.LOGIN_BTN_BY_ID)))
        submit.click()
        # time.sleep(1)
        # 获取验证码图片
        image1 = self.get_verify_image('captcha3.png')
        # 点按呼出缺口
        slider = self.get_slider()
        slider.click()
        # 获取带缺口的验证码图片
        image2 = self.get_verify_image('captcha4.png')
        # 获取缺口位置
        gap = self.get_gap(image1, image2)
        print('缺口位置', gap)
        # 减去缺口位移
        gap -= settings.BORDER
        # 获取移动轨迹
        track = self.get_track(gap)
        print('滑动轨迹', track)
        # 拖动滑块
        self.move_to_gap(slider, track)
        # return "success"

    def crack(self):
        # 输入用户名密码
        self.open()
        # 点击验证按钮

        button = self.get_verify_button()
        if button:
            button.click()
        self.login()
        # # 获取验证码图片
        # image1 = self.get_verify_image('captcha3.png')
        # # 点按呼出缺口
        # slider = self.get_slider()
        # slider.click()
        # # 获取带缺口的验证码图片
        # image2 = self.get_verify_image('captcha4.png')
        # # 获取缺口位置
        # gap = self.get_gap(image1, image2)
        # print('缺口位置', gap)
        # # 减去缺口位移
        # gap -= BORDER
        # # 获取移动轨迹
        # track = self.get_track(gap)
        # print('滑动轨迹', track)
        # # 拖动滑块
        # self.move_to_gap(slider, track)

        success = self.wait.until(
            EC.text_to_be_present_in_element(
                (By.CLASS_NAME, settings.PASSED_VALIDATION_BY_CLASS), '验证成功'))
        print(success)

        # 失败后重试
        if not success:
            self.crack()
        else:
            self.login()


if __name__ == '__main__':
    crack = CrackGeetest()
    crack.crack()
