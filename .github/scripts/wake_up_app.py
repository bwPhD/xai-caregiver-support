#!/usr/bin/env python3
"""
Streamlit 应用自动唤醒脚本
使用 Selenium 模拟真实用户访问，保持应用活跃状态
"""

import os
import sys
import time
import logging
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
import requests

class StreamlitWakeUp:
    def __init__(self, app_url, max_retries=3, timeout=30):
        self.app_url = app_url
        self.max_retries = max_retries
        self.timeout = timeout
        self.setup_logging()

    def setup_logging(self):
        """设置日志记录"""
        log_dir = os.path.join(os.path.dirname(__file__), '..', 'logs')
        os.makedirs(log_dir, exist_ok=True)

        log_file = os.path.join(log_dir, 'wake_up.log')

        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)

    def create_driver(self):
        """创建 Chrome WebDriver"""
        try:
            chrome_options = Options()
            chrome_options.add_argument('--headless')  # 无头模式
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

            # 在 GitHub Actions 中使用系统 Chrome
            if os.getenv('GITHUB_ACTIONS'):
                chrome_options.add_argument('--disable-web-security')
                chrome_options.add_argument('--allow-running-insecure-content')

            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)

            self.logger.info("Chrome WebDriver 创建成功")
            return driver

        except Exception as e:
            self.logger.error(f"创建 WebDriver 失败: {str(e)}")
            raise

    def wait_for_page_load(self, driver):
        """等待页面加载完成"""
        try:
            # 等待 Streamlit 应用的标志性元素出现
            WebDriverWait(driver, self.timeout).until(
                lambda d: d.execute_script('return document.readyState') == 'complete'
            )

            # 等待 Streamlit 特有的元素
            selectors_to_try = [
                'div[data-testid="stApp"]',
                '.main',
                'body',
                'div[data-testid="stSidebar"]'
            ]

            for selector in selectors_to_try:
                try:
                    element = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    self.logger.info(f"找到页面元素: {selector}")
                    break
                except TimeoutException:
                    continue
            else:
                self.logger.warning("未找到预期的页面元素，但页面似乎已加载")

        except TimeoutException:
            self.logger.error("页面加载超时")
            raise

    def interact_with_app(self, driver):
        """与应用进行交互以确保完全唤醒"""
        try:
            # 轻微滚动页面
            driver.execute_script("window.scrollTo(0, 100);")
            time.sleep(1)
            driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(1)

            # 尝试点击页面上的交互元素
            try:
                # 查找可能的按钮或输入框
                clickable_elements = driver.find_elements(By.CSS_SELECTOR,
                    'button, input[type="text"], input[type="number"], textarea, select')

                if clickable_elements:
                    # 点击第一个可点击元素（如果安全的话）
                    first_element = clickable_elements[0]
                    if first_element.is_displayed() and first_element.is_enabled():
                        # 记录元素信息但不实际点击，避免意外操作
                        self.logger.info(f"发现可点击元素: {first_element.tag_name} - {first_element.get_attribute('class') or 'no-class'}")
            except Exception as e:
                self.logger.info(f"元素交互检查完成 (无需操作): {str(e)}")

            # 等待应用完全响应
            time.sleep(3)

            self.logger.info("应用交互完成")

        except Exception as e:
            self.logger.warning(f"应用交互过程中出现问题: {str(e)}")

    def check_app_health(self):
        """通过 HTTP 请求检查应用健康状态"""
        try:
            response = requests.get(self.app_url, timeout=10)
            if response.status_code == 200:
                self.logger.info(f"应用健康检查通过 - 状态码: {response.status_code}")
                return True
            else:
                self.logger.warning(f"应用健康检查失败 - 状态码: {response.status_code}")
                return False
        except Exception as e:
            self.logger.warning(f"应用健康检查异常: {str(e)}")
            return False

    def wake_up_app(self):
        """执行唤醒操作"""
        self.logger.info(f"开始唤醒 Streamlit 应用: {self.app_url}")
        self.logger.info(f"当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # 首先进行健康检查
        if not self.check_app_health():
            self.logger.warning("健康检查失败，但继续尝试 Selenium 访问")

        driver = None
        try:
            driver = self.create_driver()
            self.logger.info("正在访问应用...")

            driver.get(self.app_url)
            self.wait_for_page_load(driver)
            self.interact_with_app(driver)

            # 验证页面标题
            title = driver.title
            self.logger.info(f"页面标题: {title}")

            # 检查是否成功加载 Streamlit 应用
            if "Streamlit" in title or "streamlit" in driver.page_source.lower():
                self.logger.info("✅ 应用唤醒成功!")
                return True
            else:
                self.logger.warning("⚠️ 页面加载完成，但未检测到 Streamlit 应用特征")
                return True  # 仍然算成功，因为页面加载了

        except Exception as e:
            self.logger.error(f"唤醒过程中出错: {str(e)}")
            return False

        finally:
            if driver:
                try:
                    driver.quit()
                    self.logger.info("WebDriver 已关闭")
                except Exception as e:
                    self.logger.warning(f"关闭 WebDriver 时出错: {str(e)}")

    def run(self):
        """主运行函数，包含重试逻辑"""
        success = False

        for attempt in range(1, self.max_retries + 1):
            try:
                self.logger.info(f"尝试唤醒应用 (尝试 {attempt}/{self.max_retries})")

                if self.wake_up_app():
                    success = True
                    self.logger.info(f"🎉 第 {attempt} 次尝试成功!")
                    break
                else:
                    self.logger.warning(f"第 {attempt} 次尝试失败")

            except Exception as e:
                self.logger.error(f"第 {attempt} 次尝试出现异常: {str(e)}")

            if attempt < self.max_retries:
                wait_time = 30 * attempt  # 递增等待时间
                self.logger.info(f"等待 {wait_time} 秒后重试...")
                time.sleep(wait_time)

        if success:
            self.logger.info("✅ 应用唤醒任务完成!")
            return 0
        else:
            self.logger.error("❌ 应用唤醒任务失败!")
            return 1


def main():
    """主函数"""
    app_url = os.getenv('STREAMLIT_URL')

    if not app_url:
        print("❌ 错误: 未设置 STREAMLIT_URL 环境变量")
        print("请在 GitHub Secrets 中设置 STREAMLIT_URL")
        sys.exit(1)

    print(f"🚀 开始唤醒 Streamlit 应用: {app_url}")

    wake_up = StreamlitWakeUp(app_url)
    exit_code = wake_up.run()

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
