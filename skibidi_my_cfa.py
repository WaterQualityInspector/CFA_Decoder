import datetime
import random
import re
import requests
import selenium
import time
from requests import session


def code_gen(store_number: str, dont_care_about_dine_type: bool = False, want_dine_in_only: bool = True) -> list:
    # Last three digits of the order number on the receipt, e.g. 5222632 --> 632. So 000-999.
    order_num = str(random.randint(0, 999)).zfill(3)

    # Two digits: Revenue Center -- 01,03: Dine-in, 02: Drive-Thru
    if dont_care_about_dine_type:
        dine_type = random.choice(["01", "02", "03"])
    elif want_dine_in_only:
        # Not sure what the difference is, but don't really matter
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
    sequence_3 = str(datetime.date.today().strftime("%m%d"))

    ##########################################################################
    # last digit of the current year, so if 2019, then 9.
    year_digit = str(datetime.date.today().strftime("%Y")[-1])

    def luhn_checkdigit(preceding_code_str):
        total = 0
        # Reverse the code-- flip left/right.
        reversed_code = preceding_code_str[::-1]

        for i, digit in enumerate(reversed_code):
            n = int(digit)

            # Double every second digit from the left, or originally right
            if i % 2 == 1:
                n *= 2
                # If doubling results in a number > 9, subtract 9
                if n > 9:
                    n -= 9

            total += n

        # Return the checkdigit (total modulo 10)
        return str((10 - (total % 10)) % 10)

    preceding_sequence = sequence_0 + sequence_1 + sequence_2 + sequence_3 + year_digit
    checkdigit = luhn_checkdigit(preceding_sequence)

    sequence_4 = year_digit + checkdigit
    ##########################################################################

    result = [sequence_0, sequence_1, sequence_2, sequence_3, sequence_4]

    return result


# Have not touched the section here below, it's a skeleton code. WIP

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
