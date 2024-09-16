import requests
from selenium import webdriver
import datetime
from datetime import timedelta
import re
from requests import session
from queue import SimpleQueue
from threading import Thread
import time
import multiprocessing as mp
import random
import math
import json
import sys
import os


# ********** Proxy Websites ***********
US_PROXIES = 'https://us-proxy.org/'
GATHER_PROXIES = 'https://proxygather.com/proxylist/country/?c=United%20States'
PROXY_FISH_PROXIES = 'https://www.proxyfish.com/proxylist/all_usa_proxies.php'
SPYS_PROXIES = 'http://spys.one/free-proxy-list/US/'


# ********** Code Parameters *********
PROXY_REQUESTS_BEFORE_RELOAD = 7  # Number of times a proxy is used before it is trashed
THREAD_NUMBER = 50  # Number of threads running at any given time
KNOWN_CODES = []  # Codes known (helps improve algorithm
MAX_ORDERS_PER_MIN = 8  # Maximum number of orders through the drive through in any given minute


# ********* Code Generator Helper Functions ***********
def luhn_checksum(card_number):
    def digits_of(n):
        return [int(d) for d in str(n)]
    digits = digits_of(card_number)
    even_digits = digits[-1::-2]
    odd_digits = digits[-2::-2]
    checksum = 0
    checksum += sum(odd_digits)
    for d in even_digits:
        checksum += sum(digits_of(d*2))
    return (checksum*9) % 10    

def validate_code(known_codes, test_code, max_orders_per_min, initial_time):
    if test_code[1] not in known_codes:
        return True
    
    test_time, test_num = test_code[1]*60 + int(test_code[2]), test_code[0]
    known_code_times = [int(known_code[2][2:]) + 60*int(known_code[2][:2]) for known_code in known_codes[test_code[1]]]
    known_code_nums = [int(known_code[0][:3]) for known_code in known_codes[test_code[1]]]
    
    for n in range(len(known_code_nums)):  
        if known_code_times[n] >= test_time and (n == 0 or known_code_times[n - 1] < test_time):
            while test_num > known_code_nums[n]:
                test_num -= 1000
            if test_num < known_code_nums[n] - max_orders_per_min * (known_code_times[n] - test_time + 1):
                return False
            if n == 0:
                return True
            while test_num < known_code_nums[n - 1]:
                test_num += 1000
            return test_num <= known_code_nums[n - 1] + max_orders_per_min * (test_time - known_code_times[n - 1])
    
    while test_num < known_code_nums[-1]:
        test_num += 1000
    
    return test_num <= known_code_nums[-1] + max_orders_per_min * (test_time - known_code_times[-1])


def sort_in_place(code_list):
    code_set = set()
    for code in code_list:
        code_set.add(''.join(code))
    unique_code_list = list(code_set)
    sorting_codes = []
    for code in unique_code_list:
        sorting_codes.append([code[:7], code[7:12], code[12:16], code[16:20], code[20:]])
    sorting_codes.sort(key=lambda a: a[2])
    i = 0
    while i < len(code_list):
        if i < len(sorting_codes):
            code_list[i] = sorting_codes[i]
            i += 1
        else:
            del code_list[i]
# ****************************************


#**************Code Generators ***********
def code_gen_v2(stores, known_code, max_codes_per_minute=12, minutes=20, negative=False):
    f_seven_initial, store_code, initial_time, date_string, last_2 = known_code
    initial_order_number = int(f_seven_initial[:3])
    initial_minute, initial_hour = int(initial_time[2:]), int(initial_time[:2])
    year_string = last_2[0]
    store = stores[store_code]
    if negative:
        adjustment = -1
        adjustment_bool = 1
    else:
        adjustment = 1
        adjustment_bool = 0
    
    for minute in range(minutes):
        for order_type, registers in store.items():
            for register in registers:
                for order_number in range(initial_order_number + adjustment, initial_order_number + adjustment * max_codes_per_minute*(minute + 1), adjustment):
                    code_hour = initial_hour + (initial_minute + adjustment * minute )//60
                    if code_hour >= 22 or code_hour < 6:
                        yield StopIteration
                    else:
                        code_min = (initial_minute + adjustment * minute) % 60
                        code_min = str(code_min).zfill(2)
                        code_hour = str(code_hour).zfill(2)
                        order_num_string = str(order_number%1000).zfill(3)
                        f_seven = order_num_string + order_type + register
                        final_time = code_hour + code_min
                        checksum = luhn_checksum(f_seven + store_code + final_time + date_string + year_string)
                        yield [f_seven, store_code, final_time, date_string, year_string + str(checksum)]
        


def randomize_code_gen(non_random_code_gen, random_length=1000):
    done = False
    while not done:
        code_list = []
        for _ in range(random_length):
            try:
                code_list.append(next(non_random_code_gen))
            except StopIteration:
                done=True
                break
        random.shuffle(code_list)
        
        for code in code_list:
            yield code


def offset_code_generator(days_in_past=1, start_hour=7, end_hour=20, known_codes=[], start_number=0, stores=None):
    if stores is None:
        with open('Stores.json') as f:
            js = f.read().replace('\n', '')
            stores = json.loads(js)
    
    alpha_start = 0
    total_options = 0
    for store, order_types in stores.items():
        for order_type, registers in order_types.items():
            for register in registers:
                total_options += 1
    adjustment = (end_hour - start_hour)*60*total_options
    while (alpha_start + 1) * adjustment < start_number:
        alpha_start += 1
    
    for alpha in range(alpha_start, 1000):
        for time_counter in range(60*(end_hour - start_hour)):
            for store, order_types in stores.items():
                for order_type, registers in order_types.items():
                    for register in registers:
                            # Output is orderNum, Hour, Min, register, order_type
                            yield (alpha + time_counter)%1000, start_hour + time_counter//60, time_counter%60, register, order_type, store


def ordered_code_gen(days_in_past=1, start_hour=7, end_hour=20, known_codes=[], start_number=0, stores=None):
    potential_codes = offset_code_generator(days_in_past=days_in_past, start_hour=start_hour, 
                                            end_hour=end_hour, known_codes=known_codes, 
                                            start_number=start_number, stores=stores)
    
    for code in potential_codes:
        if validate_code(known_codes, code, MAX_ORDERS_PER_MIN, initial_time=start_hour*60):
            yield code


def pseudo_random_code_gen(days_in_past=1, start_hour=7, end_hour=20, stores=None,
                           known_codes=[], start_number=0, non_random_code_gen=ordered_code_gen):
    if stores is None:
        with open('Stores.json') as f:
            js = f.read().replace('\n', '')
            stores = json.loads(js)
    
    ordered_codes = non_random_code_gen(days_in_past=days_in_past, start_hour=start_hour, stores=stores,
                                     start_number=start_number, end_hour=end_hour, known_codes=known_codes)
    
    yesterday = datetime.date.today() - timedelta(days=days_in_past)
    date_string = yesterday.strftime("%m%d")
    year = str(yesterday.strftime("%y"))[-1]
    
    total_options = 0
    for store, order_types in stores.items():
        for order_type, registers in order_types.items():
            for register in registers:
                total_options += 1
    total_time = (end_hour - start_hour)*60
    randomized_length = total_options*total_time*2
    
    while True:
        code_list = []
        for n in range(randomized_length):
            code_list.append(next(ordered_codes))
        random.shuffle(code_list)
        for code in code_list:
            orderNum = str(code[0]).zfill(3)
            time = str(code[1]).zfill(2) + str(code[2]).zfill(2)
            f_seven = orderNum + str(code[4]).zfill(2) + str(code[3]).zfill(2)
            store_code = code[5]
            check_sum = luhn_checksum(''.join([f_seven, store_code, time, date_string, year]))
            output = [f_seven, store_code, time, date_string, year + str(check_sum)]
            yield output
# ****************************************


# ************* Proxy Generators *************** 
def parse_US_PROXIES(elite=True):
    data = requests.get(US_PROXIES).text
    
    if elite:
        elite_regex = r'(?:elite proxy|anonymous)'
    else:
        elite_regex = r'\b\w+\b'
    regex_code = f'<td>([0-9\.]+?)</td><td>([0-9]+?)</td><td>US</td><td.*?>.*?</td><td>{elite_regex}</td>'
    
    proxy_list = []
    row_list = re.findall('<tr[^>]*?>(.*?)</tr>', data, re.DOTALL)
    for row in row_list:
        match = re.search(regex_code, row, flags=re.DOTALL)
        if match is not None:
            ip, port = match.group(1), match.group(2)
            if ip is not None and port is not None:
                proxy_list.append((ip, port))
    return proxy_list


def parse_FISH_PROXIES(elite=True, driver=None):
    if driver is None:
        options = webdriver.FirefoxOptions()
        options.add_argument('-headless')
        driver = webdriver.Firefox(service_log_path='NUL', options=options)
    driver.get(PROXY_FISH_PROXIES)
    time.sleep(5)
    data = driver.page_source
    data_table = re.search('(<tbody>.*?</tbody>)', data, re.DOTALL).group(1)
    proxy_list = []
    if elite:
        elite_code=r'(?:Elite|Anonymous)'
    else:
        elite_code=r'\b\w+\b'
    rows = re.findall('<tr[^>]*?>.*?</tr>', data_table)
    for row in rows:
        if "HTTP" not in row:
            continue
        if elite:
            elite_match = re.search(r'(?:Elite|Anonymous)', row)
            if elite_match is None:
                continue
        match = re.search(f'<tr.*?>.*?<td>([0-9\.]+?)</td><td>([0-9]+?)</td>', row)
        if match is not None:
            ip, port = match.group(1), match.group(2)
            proxy_list.append((ip, port))
    return proxy_list


def parse_GATHER_PROXIES(elite=True):
    payload = {'submit':'Show Full List', 'Country':'united states', 'PageIdx':'1'}
    response = requests.post(GATHER_PROXIES, payload, timeout=15).text
    entry_number = re.search('WE HAVE ([0-9]{2,4}) UNITED STATES PROXIES', response)
    entry_number = int(entry_number.group(1))
    proxy_list = []
    if elite:
        elite_regex = '(?:Elite|Anonymous)'
    else:
        elite_regex = r'\b\w+\b'
    for page in range(entry_number//30 + 1):
        payload = {'submit':'Show Full List', 'Country':'united states', 'PageIdx':str(page)}
        response = requests.post(GATHER_PROXIES, payload, timeout=10).text
        data_table = re.search('<table.+?>(.*?)</table>', response, flags=re.DOTALL).group(1)
        row_list = re.findall('<tr[^>]*?>(.*?)</tr>', data_table, re.DOTALL)
        for row in row_list:
            match = re.search(f"<td><script>document.write\('([0-9\.]+?)'\)</script></td>.*?<script>document.write\(gp.dep\('([0-9A-Fa-f]+?)'\)\)</script></td>.*?{elite_regex}</td>", row, flags=re.DOTALL)
            if match is not None:
                ip, port = match.group(1), match.group(2)
                if ip is not None and port is not None:
                    proxy_list.append((ip, str(int(port, 16))))
    return proxy_list


def parse_SPYS_PROXIES(driver=None, elite=True):
    if driver is None:
        options = webdriver.FirefoxOptions()
        options.add_argument('-headless')
        driver = webdriver.Firefox(service_log_path='NUL', options=options)
    driver.get(SPYS_PROXIES)
    time.sleep(2)
    el = driver.find_element_by_id('xf5')
    for option in el.find_elements_by_tag_name('option'):
        if option.text == 'HTTP':
            option.click() # select() in earlier versions of webdriver
            break
    time.sleep(2)
    el = driver.find_element_by_id('xpp')
    for option in el.find_elements_by_tag_name('option'):
        if option.text == '500':
            option.click() # select() in earlier versions of webdriver
            break
    if elite:
        time.sleep(2)
        el = driver.find_element_by_id('xf1')
        for option in el.find_elements_by_tag_name('option'):
            if option.text == 'A+H':
                option.click() # select() in earlier versions of webdriver
                break
    time.sleep(7)
    data = driver.page_source
    ip_list= re.findall('<tr.*?><td.*?>.*?([0-9\.]+?)<script.*?>.*?</script>.*?</font>([0-9]+?)</font></td>', data)
    proxy_list = []
    for pair in ip_list:
        ip, port = pair
        if ip is not None and port is not None:
            proxy_list.append((ip, port))
    return proxy_list


def proxy_generator(validate=True, hidden=True):
    print("Building Initial List")
    try:
        options = webdriver.FirefoxOptions()
        options.add_argument('-headless')
        driver = webdriver.Firefox(service_log_path='NUL', options=options)
        current_us_proxies = parse_US_PROXIES(elite=hidden)
        try:
            current_gather_proxies = parse_GATHER_PROXIES(elite=hidden)
        except Exception as e:
            print("Gather proxies failed to parse.")
            current_gather_proxies = []
        if not isinstance(current_gather_proxies, list):
            print("Gather proxies is not a list, resetting")
            print(f"Gather proxies: {current_gather_proxies}")
            current_gather_proxies = []
        current_fish_proxies = parse_FISH_PROXIES(elite=hidden, driver=driver)
        current_spy_proxies = parse_SPYS_PROXIES(elite=hidden, driver=driver)
        current_proxies = current_us_proxies + current_gather_proxies + current_fish_proxies + current_spy_proxies
        proxy_len = len(current_proxies)
    finally:
        driver.quit()
    counter = 0
    print(f"Proxy length: {proxy_len}")
    while True:
        proxy = current_proxies[counter % proxy_len]
        test_proxy = {'http': ':'.join(proxy)}
        if not validate or counter // proxy_len > 1 or check_proxy(test_proxy):
            yield test_proxy
            counter += 1
        else:
            print("Proxy validation failed")
            current_proxies.pop(counter % proxy_len)
            proxy_len -= 1
        if counter // (3*proxy_len) > 0:
            print("Rebuilding List")
            try:
                options = webdriver.FirefoxOptions()
                options.add_argument('-headless')
                driver = webdriver.Firefox(service_log_path='NUL', options=options)
                current_us_proxies = parse_US_PROXIES(elite=hidden)
                current_gather_proxies = parse_GATHER_PROXIES(elite=hidden)
                current_fish_proxies = parse_FISH_PROXIES(elite=hidden, driver=driver)
                current_spy_proxies = parse_SPYS_PROXIES(elite=hidden, driver=driver)
                current_proxies = current_us_proxies + current_gather_proxies + current_fish_proxies + current_spy_proxies
                counter = 0
                proxy_len = len(current_proxies)
                print(f"Proxy length: {proxy_len}")
            finally:
                driver.quit()
# **************************************************************


# ************** Proxy Generator Helper Functions ********************
def check_proxy(proxy):
    try:
        requests.get('https://api.ipify.org', proxies=proxy, timeout=5).text
        return True
    except Exception as e:
        print(f"Failed Proxy: {proxy}")
        return False


def session_creator(proxy_gen=None):
    if proxy_gen is not None:
        s = session()
        s.proxies.update(next(proxy_gen))
        return s
    else:
        return session()
# ***********************************************


# ***************** Code Checker Function *********************
def new_code_check(code, s):
    s.cookies.clear()
    c_result = s.get('https://www.mycfavisit.com/', timeout=10).text
    c_result = c_result.split('\n')
    c = ''
    for r in c_result:
        if 'Survey.aspx?c=' in r:
            c = r.split('c=')[1].split('"')[0]
            break
    payload = {'JavaScriptEnabled':'1', 'FIP':'True', 'CN1':code[0], 'CN2':code[1], 'CN3':code[2], 'CN4':code[3], 'CN5':code[4], 'NextButton':'Start', 'AllowCapture':''}
    request_url = 'https://www.mycfavisit.com/Survey.aspx?c=' + c
    response = s.post(request_url, data=payload, timeout=10).text
    if 'Unfortunately, we are unable to continue the survey based on the information you entered.' in response:
        return False
    elif 'Please rate your overall satisfaction with your most recent visit to this' in response:
        return True
    elif 'Our records indicate you have already completed a survey.' in response:
        print(f"Code {code} has already been filled out")
        return True
    elif 'Sorry, we are unable to continue the survey based' in response:
        print(f"Something went wrong on code: {code}")
        raise IndexError("Code generator broken")
    elif 'Unfortunately, the invitation is no longer valid' in response:
        print(f"Code too old to be checked: {code}")
        raise IndexError("Check codes no more than 3 days ago.")
    else:
        print(response)
        raise IOError('Loaded Unexpected Page')
# *********************************************************


# ******************** Multithreading Implementation *************************
class ThreadRipper(Thread):
    def __init__(self, run_queue, proxy_queue, output_queue, session):
        super().__init__()
        self.run_queue = run_queue
        self.proxy_queue = proxy_queue
        self.session = session
        self.output_queue = output_queue
    
    def run(self):
        counter = 0 
        if not self.session.proxies:
            next_proxy = self.proxy_queue.get()
            self.session.proxies.update(next_proxy)
        while True:
            code = self.run_queue.get()
            if counter >= PROXY_REQUESTS_BEFORE_RELOAD:
                counter = 0
                next_proxy = self.proxy_queue.get()
                self.session.proxies.update(next_proxy)
            try:
                result = new_code_check(code, self.session)
                if result:
                    print(f"Code success: {code}")
                    self.output_queue.put(code)
            except Exception as e:
                print(f"Error: {e}")
                print(f"Error on code: {code}")
            counter += 1


class ProxyThreadRipper(Thread):
    def __init__(self, validation_queue, proxy_queue):
        super().__init__()
        self.validation_queue = validation_queue
        self.proxy_queue = proxy_queue
    def run(self):
        while True:
            if self.proxy_queue.qsize() > 50 + THREAD_NUMBER:
                time.sleep(0.5)
                continue
            proxy = self.validation_queue.get()
            if check_proxy(proxy):
                self.proxy_queue.put(proxy)
# *****************************************


# ****************** Main Function ***************************
def v_2_test(seed_codes):
    run_queue = SimpleQueue()
    proxy_queue = SimpleQueue()
    output_queue = SimpleQueue()
    
    
    proxy_gen = proxy_generator(validate=False)
    proxy_validation_queue = SimpleQueue()
    for _ in range(50 + THREAD_NUMBER):
        proxy_validation_queue.put(next(proxy_gen))
        
    validation_threads = []
    for n in range(THREAD_NUMBER//PROXY_REQUESTS_BEFORE_RELOAD + 1):
        new_thread = ProxyThreadRipper(proxy_validation_queue, proxy_queue)
        new_thread.daemon = True
        new_thread.start()
        validation_threads.append(new_thread)
    
    threads = []
    for n in range(THREAD_NUMBER):
        sesh = session_creator(proxy_gen=proxy_gen)
        new_thread = ThreadRipper(run_queue, proxy_queue, 
                                  output_queue, sesh)
        new_thread.daemon = True
        new_thread.start()
        threads.append(new_thread)
    
    code_gens = []
    known_codes = []
    for seed_code in seed_codes:
        code_gens.append(randomize_code_gen(code_gen_v2(stores, seed_code)))
        code_gens.append(randomize_code_gen(code_gen_v2(stores, seed_code, negative=True)))
    date_string = seed_code[0][3]
    
    run_counter = 0
    proxy_counter = 0
    
    output_file_full = os.path.join('Raw_Codes', 'Output_full.csv')
    unused_file = os.path.join('Raw_Codes', 'Unused_codes.csv')
    date_file = os.path.join('Raw_Codes', f'Output_{date_string}.csv')
    output_files = [output_file_full, unused_file, date_file]
    
    output_counter = 0
    print("Beginning to check codes")
    done = False
    while not done:
        if proxy_validation_queue.qsize() < (50 + THREAD_NUMBER)//2:
            proxy_counter += 1
            if proxy_counter % 40 == 0:
                print(f"Entering more proxies, now at {25*proxy_counter} proxies.")
            for _ in range(25):
                proxy_validation_queue.put(next(proxy_gen))
        
        if run_queue.qsize() < 250 and len(code_gens) != 0:
            run_counter += 1
            if run_counter % 10 == 0:
                print(f"Loading more codes, now at {250*run_counter} codes.")
            for _ in range(250//len(code_gens)):
                i = 0
                while i < len(code_gens):
                    try:
                        next_code = next(code_gens[i])
                        i += 1
                    except StopIteration:
                        print("We ran out of elements for a known code sequence.")
                        code_gens.pop(i)
                        if len(code_gens) == 0:
                            print("No more known sequences, ending generation")
                            done = True
                            break
                        next_code = next(code_gens[i])
                    
                    run_queue.put(next_code)
        
        if output_queue.qsize() > 0:
            good_result = output_queue.get()
            
            good_result_string = ','.join(good_result)
            repeated_result = False
            for line in open(output_file_full):
                if line[:-1] == good_result_string:
                    repeated_result = True
                    break
            
            if repeated_result:
                print(f"We have repeated code: {good_result}")
            else:
                output_counter += 1
                if good_result[2] > seed_codes[0][2]:
                    code_gens[0] = randomize_code_gen(code_gen_v2(stores, good_result))
                else:
                    code_gens[1] = randomize_code_gen(code_gen_v2(stores, good_result, negative=True))
                print("\n\n*****************We have output*****************\n\n")
                for file in output_files:
                    with open(file, 'a+') as f:
                        f.write(good_result_string + '\n')
            if output_counter >= number:
                done = True
        
        time.sleep(0.125)


    
def single_process_main(all_stores_code_list, start_number=0, start_hour=7, end_hour=20, day_delta=1, stores=None, number=sys.maxsize):    
    yesterday = datetime.date.today() - timedelta(days=day_delta)
    date_string = yesterday.strftime("%m-%d")
    
    store_code_dict = {}
    
    if yesterday.weekday() == 6:
        raise ValueError("You are looking for codes on a Sunday. You will not find any.")
    if day_delta > 3:
        raise ValueError("You are looking for codes more than 3 days in the past. Codes this old will not be accepted.")
    elif day_delta < 0:
        raise ValueError("You are looking for codes in the future. You will not find any.")
    
    run_queue = SimpleQueue()
    proxy_queue = SimpleQueue()
    output_queue = SimpleQueue()
    
        
    proxy_gen = proxy_generator(validate=False)
    proxy_validation_queue = SimpleQueue()
    for _ in range(50 + THREAD_NUMBER):
        proxy_validation_queue.put(next(proxy_gen))
        
    validation_threads = []
    for n in range(THREAD_NUMBER//PROXY_REQUESTS_BEFORE_RELOAD + 1):
        new_thread = ProxyThreadRipper(proxy_validation_queue, proxy_queue)
        new_thread.daemon = True
        new_thread.start()
        validation_threads.append(new_thread)
    
    threads = []
    for n in range(THREAD_NUMBER):
        sesh = session_creator(proxy_gen=proxy_gen)
        new_thread = ThreadRipper(run_queue, proxy_queue, 
                                  output_queue, sesh)
        new_thread.daemon = True
        new_thread.start()
        threads.append(new_thread)
    
    store_code_dict = {}
    for code in all_stores_code_list:
        if code[1] in store_code_dict:
            store_code_dict[code[1]].append(code)
        else:
            store_code_dict[code[1]] = [code]
    for code_list in store_code_dict.values():
        sort_in_place(code_list)

    code_gens = []
    known_codes = []
    code_gens.append(pseudo_random_code_gen(known_codes=store_code_dict, start_number=start_number, stores=stores,
                                            days_in_past=day_delta, start_hour=start_hour, end_hour=end_hour))
    
    run_counter = 0
    proxy_counter = 0
    
    output_file_full = os.path.join('Raw_Codes', 'Output_full.csv')
    unused_file = os.path.join('Raw_Codes', 'Unused_codes.csv')
    date_file = os.path.join('Raw_Codes', f'Output_{date_string}.csv')
    output_files = [output_file_full, unused_file, date_file]
    
    output_counter = 0
    
    print("Beginning to check codes")
    done = False
    while not done:
        if proxy_validation_queue.qsize() < (50 + THREAD_NUMBER)//2:
            proxy_counter += 1
            if proxy_counter % 40 == 0:
                print(f"Entering more proxies, now at {25*proxy_counter} proxies.")
            for _ in range(25):
                proxy_validation_queue.put(next(proxy_gen))
        
        if run_queue.qsize() < 250:
            run_counter += 1
            if run_counter % 10 == 0:
                print(f"Loading more codes, now at {250*run_counter} codes.")
            for _ in range(250):
                try:
                    next_code = next(code_gens[0])
                except StopIteration:
                    print("We ran out of elements for a known code sequence.")
                    code_gens.pop(0)
                    next_code = next(code_gens[0])
                run_queue.put(next_code)
        
        if output_queue.qsize() > 0:
            good_result = output_queue.get()
            if good_result[1] in store_code_dict:
                validate_code_list = store_code_dict[good_result[1]]
            else:
                validate_code_list = []
            
            good_result_string = ','.join(good_result)
            repeated_result = False
            for line in open(output_file_full):
                if line[:-1] == good_result_string:
                    repeated_result = True
                    break
            
            if repeated_result or good_result in validate_code_list:
                print(f"We have repeated code: {good_result}")
            else:
                output_counter += 1
                validate_code_list.append(good_result)
                sort_in_place(validate_code_list)
                store_code_dict[good_result[1]] = validate_code_list
                print("\n\n*****************We have output*****************\n\n")
                for file in output_files:
                    with open(file, 'a+') as f:
                        f.write(good_result_string + '\n')
            if output_counter >= number:
                done = True
        
        time.sleep(0.125)
    
    while not run_queue.empty():
        try:
           run_queue.get(False)
        except Empty:
            break
# *****************************************************


# ******************* Arguments Parsers ****************
if __name__ == "__main__":
    # Check for unknown arguments
    i = 1
    while i < len(sys.argv):
        if sys.argv[i] in ["-number", "-start"]:
            i += 2
        elif sys.argv[i] in ['-stores', '-drive_through', '-dine_in']:
            i += 1
        else:
            raise ValueError(f"Unexpected kwarg: {sys.argv[i]}")
    
    if "-stores" in sys.argv:
        store_file = sys.argv[sys.argv.index("-stores") + 1]
    elif "-drive_through" in sys.argv:
        store_file = os.path.join("Store_Files", "all_drive_through.json")
    elif "-dine_in" in sys.argv:
        store_file = os.path.join("Store_Files", "all_dine_in.json")
    else:
        store_file = os.path.join("Store_Files", "all_stores.json")
    
    if "-number" in sys.argv:
        number = int(sys.argv[sys.argv.index("-number") + 1])
    else:
        number = sys.maxsize
    
    if "-start" in sys.argv:
        s_number = int(sys.argv[sys.argv.index("-start") + 1])
    else:
        s_number = 0
    
    with open(store_file) as f:
        js = f.read()
        stores = json.loads(js)
    seed_codes = [['6690202', '02536', '1652', '0226', '07'], ['8690202', '02536', '1837', '0226', '07'], 
                  ['0650202', '02536', '1858', '0226', '07'], ['4650202', '02536', '1504', '0226', '07'], 
                  ['2760202', '02536', '1359', '0226', '07']]
    # single_process_main(KNOWN_CODES, start_number=s_number, stores=stores, number=number)
    # for code in randomize_code_gen(code_gen_v2(stores, seed_code)):
    #     print(code)
    v_2_test(seed_codes)
