#!/usr/bin/env python3
"""
Streamlit App 自动唤醒脚本
自动访问 Streamlit 应用并点击唤醒按钮
"""

import os
import sys
import time
import logging
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager

# ========== 日志配置 ==========
LOG_DIR = Path(__file__).parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / "wake_up.log", encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def create_driver():
    """创建 Chrome WebDriver"""
    logger.info("初始化 Chrome WebDriver...")
    
    options = Options()
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    options.add_argument('--disable-extensions')
    options.add_argument('--disable-infobars')
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.set_page_load_timeout(60)
    
    logger.info("WebDriver 初始化成功")
    return driver


def wake_up_streamlit_app(url, max_retries=3):
    """
    唤醒 Streamlit 应用
    
    Args:
        url: Streamlit 应用 URL
        max_retries: 最大重试次数
    
    Returns:
        bool: 是否成功
    """
    for attempt in range(1, max_retries + 1):
        driver = None
        try:
            logger.info(f"第 {attempt}/{max_retries} 次尝试唤醒应用...")
            driver = create_driver()
            
            logger.info(f"访问 URL: {url}")
            driver.get(url)
            
            # 等待页面加载
            time.sleep(5)
            
            # 检查是否有唤醒按钮
            try:
                wake_button = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((
                        By.XPATH, 
                        "//button[contains(text(), 'Yes, get this app back up')]"
                    ))
                )
                logger.info("检测到唤醒按钮，正在点击...")
                wake_button.click()
                
                # 等待应用启动
                time.sleep(10)
                
                # 验证是否唤醒成功
                try:
                    WebDriverWait(driver, 30).until(
                        EC.invisibility_of_element_located((
                            By.XPATH, 
                            "//button[contains(text(), 'Yes, get this app back up')]"
                        ))
                    )
                    logger.info("✅ 应用已成功唤醒！")
                    return True
                except TimeoutException:
                    logger.warning("唤醒按钮仍然存在，可能唤醒失败")
                    
            except TimeoutException:
                # 没有找到唤醒按钮，说明应用已经是唤醒状态
                logger.info("✅ 应用已经处于唤醒状态！")
                return True
                
        except WebDriverException as e:
            logger.error(f"WebDriver 错误: {e}")
        except Exception as e:
            logger.error(f"未知错误: {e}")
        finally:
            if driver:
                try:
                    driver.quit()
                except:
                    pass
        
        if attempt < max_retries:
            logger.info(f"等待 10 秒后重试...")
            time.sleep(10)
    
    logger.error(f"❌ {max_retries} 次尝试后仍然失败")
    return False


def main():
    """主函数"""
    logger.info("=" * 50)
    logger.info("Streamlit 自动唤醒脚本启动")
    logger.info("=" * 50)
    
    # 从环境变量获取 URL
    streamlit_url = os.environ.get('STREAMLIT_URL')
    
    if not streamlit_url:
        logger.error("❌ 错误: 未设置 STREAMLIT_URL 环境变量")
        logger.error("请在 GitHub Secrets 中添加 STREAMLIT_URL")
        sys.exit(1)
    
    logger.info(f"目标 URL: {streamlit_url}")
    
    # 执行唤醒
    success = wake_up_streamlit_app(streamlit_url)
    
    if success:
        logger.info("🎉 唤醒任务完成！")
        sys.exit(0)
    else:
        logger.error("💥 唤醒任务失败！")
        sys.exit(1)


if __name__ == "__main__":
    main()
