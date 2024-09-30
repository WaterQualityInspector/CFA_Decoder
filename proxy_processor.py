import requests
import asyncio
import aiohttp
import pandas as pd
from requests.adapters import Retry
from io import StringIO

cfa_url = 'https://www.mycfavisit.com/'
test_delay = 5

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    'Connection': 'keep-alive',
    'Referer': 'https://www.google.com/',
    'Upgrade-Insecure-Requests': '1'
}

# request retry strategy
retry_strategy = Retry(
    total=10,  # Total retries
    backoff_factor=1  # A delay between retries (e.g., 1 second, then 2 seconds, etc.)
)


def fetch_proxy_subset_1():
    # github proxifly
    proxy_archive_url = "https://raw.githubusercontent.com/proxifly/free-proxy-list/main/proxies/countries/US/data.json"
    archive_response = requests.get(proxy_archive_url)
    is_proxy_fetched = False

    if archive_response.status_code == 200:
        print("Proxy List Fetched for US")
        proxy_list = archive_response.json()
        proxy_list = [entry['proxy'] for entry in proxy_list if entry['geolocation']['country'] == 'US']

        is_proxy_fetched = True
        print(len(proxy_list), proxy_list[0])
        return proxy_list
    else:
        print(f"Proxy List Request Failed!!! {archive_response.status_code}")
        return None


def fetch_proxy_subset_2():
    proxy_archive_url = "https://sunny9577.github.io/proxy-scraper/proxies.json"
    archive_response = requests.get(proxy_archive_url)
    is_proxy_fetched = False

    if archive_response.status_code == 200:
        print("Proxy List Fetched")
        proxy_df = pd.json_normalize(archive_response.json())
        country_mask_df = proxy_df['country'].str.contains('united states', case=False, na=False)
        anonymity_mask_df = proxy_df['anonymity'] != 'unknown'
        proxy_df = proxy_df[country_mask_df & anonymity_mask_df].reset_index(drop=True)[['type', 'ip', 'port']]
        proxy_df['type'] = proxy_df['type'].replace('HTTP/HTTPS', 'https')
        proxy_df['proxy_url'] = proxy_df['type'] + "://" + proxy_df['ip'] + ":" + proxy_df['port']
        proxy_list = proxy_df['proxy_url'].tolist()
        print(proxy_df)
        print(len(proxy_list))
        return proxy_list
    else:
        print(f"Proxy List Request Failed!!! {archive_response.status_code}")
        return None


def fetch_all_proxies():
    all_proxy_list = fetch_proxy_subset_1()
    all_proxy_list.extend(fetch_proxy_subset_2())
    print(f"Proxies fetched. Total {len(all_proxy_list)} US proxies available.")
    return all_proxy_list


async def test_proxy(session, proxy_url, print_out=False):
    try:
        # Make the HTTP request through the proxy
        async with session.get("https://api.ipify.org", proxy=proxy_url, timeout=10, headers=HEADERS, ssl=True) as response:
            # If successful, return the proxy URL
            if response.status == 200:
                print(f"CONNECTION SUCCESS: {proxy_url}") if print_out else None
                return proxy_url
            else:
                # If the request fails, log the failure and return "None"
                print(f"Failed Connection {proxy_url}, status code: {response.status}") if print_out else None
                return None

    # Handle various exceptions
    except (aiohttp.ClientProxyConnectionError, aiohttp.ClientConnectorError) as e:
        print(f"Error Connecting {proxy_url}: {str(e)}") if print_out else None
        return None
    except asyncio.TimeoutError:
        print(f"Error Connecting {proxy_url}: Timeout") if print_out else None
        return None
    except Exception as e:
        print(f"Unexpected Error Connecting {proxy_url}: {str(e)}") if print_out else None
        return None


async def find_working_proxy(search_proxy_list, batch_size=100, delay=5):
    working_proxy_list = []
    session = aiohttp.ClientSession()
    for i in range(0, len(search_proxy_list), batch_size):
        print(f"Index {i}, Processing {batch_size} Entries")
        proxy_list_batch = search_proxy_list[i:i + batch_size]
        tasks = [asyncio.create_task(test_proxy(session, proxy_url, print_out=True)) for proxy_url in proxy_list_batch]

        results = await asyncio.gather(*tasks)
        working_proxy_list.extend([proxy for proxy in results if proxy])
        # Add a delay to avoid spamming
        await asyncio.sleep(max(delay, 1))

    return working_proxy_list, session


async def main():
    print("boom")


asyncio.run(main())
