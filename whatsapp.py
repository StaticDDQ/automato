# -*- coding: utf-8 -*-

# Whatsapp Bot for sending Mass messages 
# Worker RabbitMQ

from selenium import webdriver 
import time 
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC 
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException
import socket
import pika 
import threading
import functools
import MySQLdb
import json
from app import db
from model import contacts , job_task

chrome_options = Options()
chrome_options.add_argument("--disable-popup-blocking")

mssg_1 = "Hi ,"
mssg_2 = "We are Mfg. of exclusive Hand Block Printed Dress Materials , Dupatta ,Stole ,Sarees , Kurties ,Fabrics , Skirts & much more ."
mssg_3 = "Please visit www.jaitexart.com"
mssg_4 = "Our customers include Fabindia , Westside, Biba, Anita dongre and much more .If you are interested in wholesale purchase (minimum order RS 15,000) . Please Contact Us."
# Double Enter
mssg_5 = "Thanking you"
mssg_6 = "Hemant sethia"
mssg_7 = "Jai texart"
mssg_8 = "Jaipur."
mssg_9 = "+918875666619"

chrome_path = r"C:\Users\padam\Downloads\chromedriver_win32\chromedriver.exe"
global first_run_check
first_run_check = 0

credentials = pika.PlainCredentials('guest' , 'guest')
connection = pika.BlockingConnection(
    pika.ConnectionParameters(host = 'localhost' , credentials = credentials))
channel = connection.channel()
channel.queue_declare(queue='mssg_queue' , durable= True)
channel.basic_qos(prefetch_count = 1)
threads = []

def driver_init():
    global driver 
    driver = webdriver.Chrome(chrome_path , chrome_options= chrome_options)

def send_mssg():
    actions = ActionChains(driver) # ActionChain init
    element = driver.find_element_by_css_selector('._1Plpp') # Selecting Input Box
    time.sleep(1) # Wait before sending mssg
    element.send_keys(mssg_1)
    actions.key_down(Keys.SHIFT)
    actions.key_down(Keys.ENTER)
    actions.key_up(Keys.ENTER)
    actions.key_up(Keys.SHIFT)
    actions.perform()
    element.send_keys(mssg_2)
    actions.key_down(Keys.SHIFT)
    actions.key_down(Keys.ENTER)
    actions.key_up(Keys.ENTER)
    actions.key_up(Keys.SHIFT)
    actions.perform()
    element.send_keys(mssg_3)
    actions.key_down(Keys.SHIFT)
    actions.key_down(Keys.ENTER)
    actions.key_up(Keys.ENTER)
    actions.key_up(Keys.SHIFT)
    actions.perform()
    element.send_keys(mssg_4)
    actions.key_down(Keys.SHIFT)
    actions.key_down(Keys.ENTER)
    actions.key_up(Keys.ENTER)
    actions.key_down(Keys.ENTER)
    actions.key_up(Keys.ENTER)
    actions.key_up(Keys.SHIFT)
    actions.perform()
    element.send_keys(mssg_5)
    actions.key_down(Keys.SHIFT)
    actions.key_down(Keys.ENTER)
    actions.key_up(Keys.ENTER)
    actions.key_up(Keys.SHIFT)
    actions.perform()
    element.send_keys(mssg_6)
    actions.key_down(Keys.SHIFT)
    actions.key_down(Keys.ENTER)
    actions.key_up(Keys.ENTER)
    actions.key_up(Keys.SHIFT)
    actions.perform()
    element.send_keys(mssg_7)
    actions.key_down(Keys.SHIFT)
    actions.key_down(Keys.ENTER)
    actions.key_up(Keys.ENTER)
    actions.key_up(Keys.SHIFT)
    actions.perform()
    element.send_keys(mssg_8)
    actions.key_down(Keys.SHIFT)
    actions.key_down(Keys.ENTER)
    actions.key_up(Keys.ENTER)
    actions.key_up(Keys.SHIFT)
    actions.perform()
    element.send_keys(mssg_9)
    
    driver.find_element_by_css_selector('._35EW6').click() #send mssg
   
def send_photo():

    attach = WebDriverWait(driver , 40).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR , "#main > header > div._1i0-u > div > div:nth-child(2)"))
        )
    attach.click()

    photo = driver.find_element_by_css_selector('#main > header > div._1i0-u > div > div.rAUz7._3TbsN > span > div > div > ul > li:nth-child(1) > input[type="file"]').send_keys('C:\\Users\\padam\\Pictures\\wpimage.jpg')
    time.sleep(1)
    photo_send = driver.find_element_by_css_selector('#app > div > div > div.MZIyP > div._3q4NP._1Iexl > span > div > span > div > div > div._2sNbV._3ySAH > span:nth-child(3) > div > div').click()
 
def is_connected():
    try:
        socket.create_connection(("www.google.com" , 80))
        return True 
    except:
        is_connected()


def check_valid_number():
    try:
        popup = driver.find_element_by_css_selector("#app > div > span:nth-child(3) > div > span > div > div > div > div")
        check_valid = popup.get_attribute("data-animate-modal-popup")
        print(check_valid)
        if check_valid :
            return False 
        else:
            return True
    except Exception as e:
        print("Number seems to be valid : " + str(e) )
        return True

def ack_message(channel , delivery_tag):
    if channel.is_open:
        channel.basic_ack(delivery_tag)
    else:
        pass

def consume_stop():
    channel.basic_cancel()

def on_message(channel , method_frame ,header_frame , body , args):
    (connection , threads) = args 
    delivery_tag = method_frame.delivery_tag
    t = threading.Thread(target= send_messages, args = (connection , channel , delivery_tag , body))
    t.start()
    threads.append(t)

def whatsapp_send(num):
    driver.get('https://web.whatsapp.com/send?phone='+num+'')
    wp_sent = db.session.query(contacts).filter_by(contact_one = str(num)).first()
    global first_run_check
    if first_run_check is 0:
        time.sleep(10)
        first_run_check = 1 
    time.sleep(20)
    if check_valid_number():
        print("Inside message block")
        send_photo()
        send_mssg()
        wp_sent.wp_cnt = 1
        db.session.commit()
        print("Sleeping for 6 secs")
        time.sleep(6) # setup for Leave page alert
        print("Wake Up , move to next")
    else:
        wp_sent.wp_cnt = -2
        db.session.commit()
        print("Not Valid : Unable to send to "+num) 

def send_messages(connection , channel , delivery_tag , body):
            
    thread_id = threading.get_ident() 
    fmt = 'Thread id: {} Delivery Tag: {} Message body: {}'
    driver_init()
    mssg_data = json.loads(body)
    city = mssg_data['city']
    task_id = mssg_data['task_id']
    meta = mssg_data['meta']
    job = db.session.query(job_task).filter_by(id= task_id).first()
    con_all = db.session.query(contacts).filter_by(city = city).filter((contacts.wp_cnt == 0) | (contacts.wp_cnt == -1)).all()
    t_num = [x.contact_one for x in con_all]
    numbers = list(set([x.contact_one for x in con_all]))
    numbers.remove('')
    # for num in numbers[100:]:
    #     if first_run_check is 0:
    #         time.sleep(10)
    #         first_run_check = 1        
    #     if is_connected():
    #         wp_sent = db.session.query(contacts).filter_by(contact_one = str(num)).first()
    #         try:        
    #             whatsapp_send(num)
    #         except Exception as e:
    #             wp_sent.wp_cnt = -1 
    #             db.session.commit()
    #             print("Unable to send to "+num)
    #             print(str(e))
    #     else:
    #         job.meta = str(num)
    #         db.session.commit()
    #         print("Internet doesn't seem to be running! CLosing down send jobs!")


    if not numbers:
        try: 
            cb = functools.partial(ack_message , channel , delivery_tag)
            connection.add_callback_threadsafe(cb)        
            job.status = 2 # Resume
            db.session.commit()
            driver.close()
            print("Task Done")
        except Exception as e:
            print("Somethign Happeded - " + str(e))
    else:

        for num in numbers[:100]:
            check_sent = db.session.query(contacts).filter_by(contact_one = str(num)).first()
            # if check_sent.wp_cnt != str(1) or str(-2) :     
            if is_connected():
                wp_sent = db.session.query(contacts).filter_by(contact_one = str(num)).first()
                try:        
                    whatsapp_send(num)
                except Exception as e:
                    wp_sent.wp_cnt = -1 
                    db.session.commit()
                    print("Unable to send to "+num)
                    print(str(e))
            else:
                job.meta = str(num)
                db.session.commit()
                print("Internet doesn't seem to be running! CLosing down send jobs!")
            # else:
            #     pass
        

        try: 
            cb = functools.partial(ack_message , channel , delivery_tag)
            connection.add_callback_threadsafe(cb)        
            job.status = 3 # Resume
            db.session.commit()
            driver.close()
            print("Task Done")
        except Exception as e:
            print("Somethign Happeded - " + str(e))
    # else:
    #     index = numbers.index(str(meta))
    #     new_numbers = numbers[index:index+100]
    #     for num in new_numbers: 
    #         if check_sent.wp_cnt != str(1) :     
    #             wp_sent = db.session.query(contacts).filter_by(contact_one = str(num)).first()   
    #             if is_connected():
    #                 try:        
    #                     whatsapp_send(num)
    #                 except Exception as e:
    #                     wp_sent.wp_cnt = -1 
    #                     db.session.commit()
    #                     print("Unable to send to "+num)
    #                     print(str(e))
    #             else:
    #                 job.meta = str(num)
    #                 db.session.commit()
    #                 print("Internet doesn't seem to be running! CLosing down send jobs!")
    #         else:
    #             pass

threads = []
on_message_callback = functools.partial(on_message , args=(connection , threads))
channel.basic_consume(on_message_callback , queue='mssg_queue')

try:
    print("consuming" )
    channel.start_consuming()
   
except KeyboardInterrupt:
    channel.stop_consuming()

for thread in threads:
    thread.join()
