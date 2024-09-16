from datetime import datetime, timedelta
import random
import re
import selenium
import time
from requests import session


def code_gen(store_number: str, day_delta: int = 2,dont_care_about_dine_type: bool = False, want_dine_in_only: bool = True) -> list:
    # Last three digits of the order number on the receipt, e.g. 5222632 --> 632. So 000-999.
    order_num = str(random.randint(0, 999)).zfill(3)

    # Two digits: Revenue Center
    # 01: Dine-in, 02: Drive-Thru, 03: Carry-Out
    # Will treat 01 and 03 the same since they are in-person.
    if dont_care_about_dine_type:
        dine_type = random.choice(["01", "02", "03"])
    elif want_dine_in_only:
        # 01 is the actual dine-in. 03 is carry-out.
        dine_type = random.choice(["01", "03"])
    else:
        dine_type = "02"

    """
    Two digits: register number -- 04, 05 , 06 and etc.
        Varies a lot from store to store, usually:
        01, 03: Dine-in = [04 to 06] (but not limited to. -- most commonly 04)
        02: Drive-Thru = [02] (Sometimes saw them in 50s)
    
    technically a random number might work?
    """
    if dine_type != "02":
        register_num = "04"
    else:
        register_num = "02"

    sequence_0 = order_num + dine_type + register_num

    #########################################################################
    # Just choosing one for now, no loops implemented yet!
    # e.g. #01336 (Store number printed near the top of the receipt)
    sequence_1 = str(store_number).zfill(5)

    #########################################################################
    # 0700 to 2100 CFA Business Hours
    hour = str(random.randint(7, 21)).zfill(2)
    minute = str(random.randint(0, 59)).zfill(2)

    # Timestamp sequence
    sequence_2 = hour + minute

    ##########################################################################
    # date = MM:DD
    yesterday = datetime.today()-timedelta(days=day_delta)

    if yesterday.weekday() == 6:
        raise ValueError("You are looking for codes on a Sunday. You will not find any. CFA isn't open..")
    if day_delta > 3:
        raise ValueError("You are looking for codes more than 3 days in the past. Codes this old will not be accepted.")
    elif day_delta < 0:
        raise ValueError("You are looking for codes in the future. You will not find any.")

    sequence_3 = str(yesterday.strftime("%m%d"))

    ##########################################################################
    # last digit of the current year, so if 2019, then 9.
    year_digit = str(yesterday.strftime("%Y")[-1])

    def luhn_checksum(preceding_code_str):
        total = 0
        # Reverse the code-- flip left/right.
        reversed_code = preceding_code_str[::-1]

        for i, digit in enumerate(reversed_code):
            n = int(digit)

            # Double every second digit from the right (or every odd index in the reversed list)
            if i % 2 == 1:
                n *= 2
                if n > 9:
                    n -= 9

            total += n

        checksum_str = str((total * 9) % 10)
        # Return the checkdigit (total modulo 10)
        return checksum_str

    preceding_sequence = sequence_0 + sequence_1 + sequence_2 + sequence_3 + year_digit
    check_sum = luhn_checksum(preceding_sequence)

    sequence_4 = year_digit + check_sum
    ##########################################################################

    result = [sequence_0, sequence_1, sequence_2, sequence_3, sequence_4]
    print(result)

    return result


# Have not touched the section here below, it's a skeleton code. WIP

def check_code(code):
    s = session()

    # Set up headers to mimic a browser
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
    }

    # Get the initial page
    c_result = s.get('https://www.mycfavisit.com/', headers=headers, timeout=10).text
    c_result = c_result.split('\n')
    c = ''
    for r in c_result:
        if 'Survey.aspx?c=' in r:
            c = r.split('c=')[1].split('"')[0]
            break

    payload = {
        'JavaScriptEnabled': '1',
        'FIP': 'True',
        'CN1': code[0],
        'CN2': code[1],
        'CN3': code[2],
        'CN4': code[3],
        'CN5': code[4],
        'NextButton': 'Start',
        'AllowCapture': ''
    }
    request_url = 'https://www.mycfavisit.com/Survey.aspx?c=' + c

    # Post the payload with headers
    response = s.post(request_url, data=payload, headers=headers, timeout=10).text

    if 'Sorry, we are unable to continue the survey based on the information you provided.' in response:
        return False
    elif 'Please rate your overall satisfaction with your most recent visit to this' in response:
        return True
    else:
        raise Exception('Hit Block Page')

check_code(code_gen("02536", 2, False, True))

"""
def check_code(code, proxy):
    s = session()
    c_result = s.get('https://www.mycfavisit.com/', timeout=10, proxies=proxy).text
    c_result = c_result.split('\n')
    c = ''
    for r in c_result:
        if 'Survey.aspx?c=' in r:
            c = r.split('c=')[1].split('"')[0]
            break
    payload = {'JavaScriptEnabled': '1', 'FIP': 'True', 'CN1': code[0], 'CN2': code[1], 'CN3': code[2], 'CN4': code[3],
               'CN5': code[4], 'NextButton': 'Start', 'AllowCapture': ''}
    request_url = 'https://www.mycfavisit.com/Survey.aspx?c=' + c
    response = s.post(request_url, data=payload, timeout=10, proxies=proxy).text
    if 'Sorry, we are unable to continue the survey based on the information you provided.' in response:
        return False
    elif 'Please rate your overall satisfaction with your most recent visit to this' in response:
        return True
    else:
        raise Exception('Hit Block Page')


def complete_survey(code, proxy):
    return 0


if __name__ == "__main__":
    main()
"""