from selenium import webdriver
import sched, time, os
from time import sleep
from selenium.webdriver.common.keys import Keys
from dotenv import load_dotenv

from selenium.webdriver.common.keys import Keys
driver = webdriver.Chrome()
refresh_time_in_seconds = 35

load_dotenv()
sportingindexusername = os.environ.get("sportingindexuname")
sportingindexpasswordenviron = os.environ.get("sportingindexpasswd")
oddsmonkeyusernameenviron = os.environ.get("oddsmonkeyusername")
oddsmonkeypasswordenviron = os.environ.get("oddsmonkeypassword")

driver.get("https://www.oddsmonkey.com/oddsmonkeyLogin.aspx?returnurl=%2f")
sleep(3)
driver.find_element_by_id("dnn_ctr433_Login_Login_DNN_txtUsername").send_keys(
    oddsmonkeyusernameenviron)
driver.find_element_by_id("dnn_ctr433_Login_Login_DNN_txtPassword").send_keys(
    oddsmonkeypasswordenviron)
driver.find_element_by_id("dnn_ctr433_Login_Login_DNN_cmdLogin").click()
sleep(54)
driver.get("https://www.oddsmonkey.com/Tools/Matchers/EachwayMatcher.aspx")
sleep(4)
driver.execute_script(
    '''window.open("https://www.sportingindex.com/fixed-odds","_blank");''')
driver.switch_to.window(driver.window_handles[-1])
# second_page = "https://www.sportingindex.com/fixed-odds"

# driver.get(second_page);
sportingindexusername = os.environ.get("sportingindexuname")
sleep(3)

driver.find_element_by_id("usernameCompact").send_keys(sportingindexusername)
driver.find_element_by_id("passwordCompact").send_keys(
    sportingindexpasswordenviron)
driver.find_element_by_id("submitLogin").click()
sleep(2)
driver.find_element_by_xpath('//a[@class="btn-my-account"]').click()

sleep(1)
driver.find_element_by_id("decimalBtn").click()
sleep(1)

driver.get(
    "https://www.sportingindex.com/fixed-odds/horse-racing/race-calendar")
sleep(3)

driver.switch_to.window(driver.window_handles[0])
driver.refresh()
sleep(4)

url = driver.current_url
while True:
    if url == driver.current_url:
        driver.refresh()
        sleep(4)
        if not driver.find_elements_by_class_name("rgNoRecords"):
            dateofracecell = driver.find_element_by_xpath(
                '//table//tr[@id="dnn_ctr1157_View_RadGrid1_ctl00__0"]//td')
            dateofrace = dateofracecell.text.lower()
            racetime = dateofrace[-5:]
            # print(dateofrace)
            racevenuecell = driver.find_element_by_xpath(
                '//table//tr[@id="dnn_ctr1157_View_RadGrid1_ctl00__0"]//td[8]')
            racevenue = racevenuecell.text.lower().strip()
            sizestring = len(racevenue)
            # Slice string to remove last 3 characters from string
            racevenue = racevenue[:sizestring - 5].strip()

            # print(racevenue)

            horsenamecell = driver.find_element_by_xpath(
                '//table//tr[@id="dnn_ctr1157_View_RadGrid1_ctl00__0"]//td[9]')
            horsename = horsenamecell.text.title()
            # print(horsename)
            # horsename = "Mliljkdsf"

            horseoddscell = driver.find_element_by_xpath(
                '//table//tr[@id="dnn_ctr1157_View_RadGrid1_ctl00__0"]//td[13]'
            )
            horseodds = horseoddscell.text

            winexchangelinkcell = driver.find_element_by_xpath(
                '//table//tr[@id="dnn_ctr1157_View_RadGrid1_ctl00__0"]//td[14]//a'
            )
            winexchangelink = winexchangelinkcell.get_attribute('href')

            # print(horseodds)

            driver.find_element_by_xpath(
                '//table//tr[@id="dnn_ctr1157_View_RadGrid1_ctl00__0"]//td[55]//div//a'
            ).click()
            # driver.find_element_by_id("submitLogin").click()

            print(dateofrace + "," + racetime + "," + racevenue + "," +
                  horsename + "," + horseodds + "," + winexchangelink)
            url = driver.current_url
            driver.switch_to.window(driver.window_handles[1])
            driver.refresh()
            # driver.get("https://www.sportingindex.com/fixed-odds/horse-racing/race-calendar")
            sleep(3)

            driver.find_element_by_link_text(racetime).click()
            sleep(3)
            # this is where we need to check if the horse is on this page - can happen if we choose event with same time but wrong location

            if (horsename not in driver.page_source):
                print("No horse found")
                driver.get(
                    "https://www.sportingindex.com/fixed-odds/horse-racing/race-calendar"
                )
                sleep(3)
                driver.switch_to.window(driver.window_handles[0])
                driver.refresh()
                sleep(4)
            else:
                #   element = elements[0]

                # if driver.find_element_by_xpath("//td[contains(text(), '" + horsename + "')]"):
                pathtohorsenamexpath = "//td[contains(text(), '" + horsename + "')]/following-sibling::td[5]/wgt-price-button/button"
                driver.find_element_by_xpath(pathtohorsenamexpath).click()
                sleep(1)
                driver.find_element_by_class_name("ng-pristine").send_keys("2")
                driver.find_element_by_xpath(
                    '// input[ @ type = "checkbox"]').click()
                driver.find_element_by_class_name("placeBetBtn").click()
                sleep(2)
                driver.find_element_by_xpath(
                    "//button[contains(text(), 'Continue')]").click()
                # clear variables
                horsename = ""
                racetime = ""
                racevenue = ""
                sleep(3)
                #    driver.find_element_by_xpath('//wgt-spin-icon[@class="close-bet"]').click()
                driver.get(
                    "https://www.sportingindex.com/fixed-odds/horse-racing/race-calendar"
                )
                sleep(2)
                driver.switch_to.window(driver.window_handles[0])
                driver.refresh()
                sleep(4)
        else:
            print("nothing to see here")
            # so no log out
            driver.switch_to.window(driver.window_handles[1])
            sleep(4)

            driver.get(
                "https://www.sportingindex.com/fixed-odds/horse-racing/race-calendar"
            )
            sleep(2)
            driver.switch_to.window(driver.window_handles[0])
            driver.refresh()
            sleep(4)
        time.sleep(refresh_time_in_seconds)
        print("waiting")
