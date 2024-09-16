# CFA Decoder. Combined and streamlined from works of Dejan992 and Anthony (a friend of mine)

## READ ME adapted from Dejan992. 
Bruteforcing our way towards ultimate customer satisfaction- free food! **(For Educational Purposes Only, Use at Your Own Discretion)**
Analyzing multiple receipts from Chick-fil-As across the country (via Google Images) allowed us to determine (roughly) the pattern used for generating the "Serial Num" occasionally found near the bottom of the customer copy receipt (see example below).

Insecurities in their [customer experience portal](https://www.mycfavisit.com) allow for these serial numbers to be verified as working in rapid succession. Once a given serial number as been verified as working, using a web browser automation library like Selenium, the customer experience survey can be completed automatically (and auto-filled with the email you'd like to have your free sandwich voucher(s) sent to).

### Example Serial Num: 6320106-01336-1109-0523-95

**Sequence 1 (7-Digits)**
- The 1-3rd digits represent the last three digits of the **Order Number**, printed near the top of the customer copy receipt (in this case, the order number was 5222**632**).
- The 4-5th digits are assumed to be the revenue center (dine-in, carry-out, drive-thru), in this case dine-in was represented by a 1 (printed below the date/time on the customer copy).
  - The string is zfilled to 2 digits, so 1 -> 01.
    - For dine-in: 01 and 03 are the most common.
    - For drive-thru: 02 is the most common.
- The 6-7th digits of this first sequence represent the register that the transaction was carried out on (printed above the cashier name on the customer copy), in this case, register 6.
  - The string is zfilled to 2 digits, so 1 -> 01.
    - For dine-in: 04, 05, and 06 are common. 04 being the most common.
    - For drive-thru: 02 is the most common. Sometimes double digits are seen depending on the locations, e.g. (56, 58, and etc).

**Sequence 2 (5-Digits)**
- The five-digit number that makes up sequence two is simply the store number printed near the top of the receipt (in this case, #01336).

**Sequence 3 & 4 (4-Digits Each)**
- Sequence 3 represents the time of the transaction (HH:MM)
- Sequence 4 represents the date that the transaction was made on (MM:DD).
- Note the time duration can be only "stored" up to two days. The expiration date for surveys are two days.

**Sequence 5 (2-Digits)**
- The first of the two digits in the last sequence is the last number of the year that the transation was made in (e.g. 2019 -> 9).
- Luhn Checkdigit to the preceding sequence of numbers. Also can be randomly generated if you feel like throwing cpu at it.
