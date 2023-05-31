import json
import utime
import devapi
import urequests as requests

wow_url = 'https://mowowprod.azure-api.net/api/Observations'
api_key = str(devapi.DEV['API_KEY'])
max_retries = 3  # number retries to be made when report submission fails
delay = 5  # delay between retries in seconds


def send_wow(wlan, ssid, password, wow_site_id, wow_auth_key,
             tempc, max_tempc=None, min_tempc=None):
    """Transmit a formatted data message to the Met Office WoW website using
    the 'canonical' API. If daily maximum and minimum temperatures are
    provided as parameters then these will be included in the report.
    Date and time is formatted as required by the WoW API.

    Normal HTTP response code will be 201 for a successful submission. If
    transmission is unsuccessful due to no wifi connection, then an
    attempt is made to reconnect to WiFi and repeat the transmission.
    A number of retries will also be made if a 201 response is not received
    (as can happen if the WoW servers are busy or down).
    Note that at times, the WoW API can be very slow to respond to requests
    and that the minimum time allowed between transmissions to WoW API
    is approx 5 mins."""

    print('preparing WoW report...')
    data = dict()
    wow_dtg = format_time(utime.localtime())
    data["reportStartDateTime"] = wow_dtg
    data["reportEndDateTime"] = wow_dtg
    data["siteId"] = wow_site_id
    data["siteAuthenticationKey"] = wow_auth_key
    data["isPublic"] = "true"
    data["isLatestVersion"] = "true"
    data["dryBulbTemperature_Celsius"] = tempc
    if max_tempc is not None:
        data["airTemperatureMax_Celsius"] = max_tempc
    if min_tempc is not None:
        data["airTemperatureMin_Celsius"] = min_tempc
    data["collectionName"] = 1
    data["observationType"] = 1
    data = json.dumps(data)
    print(data)

    headers = {
        'Ocp-Apim-Subscription-Key': api_key,
        'Content-Type': 'application/json'
    }
    # noinspection PyBroadException
    try:
        if data and tempc is not None:
            print('sending WoW...')
            number_retries = 0
            response = requests.post(wow_url, headers=headers, data=data)
            print("sent (" + str(response.status_code) + "), status = " + str(
                wlan.status()))
            response.close()
            # Retry the wow post if we don't get a 201 response
            while response.status_code != 201 and number_retries < max_retries:
                utime.sleep(delay)
                response = requests.post(wow_url, headers=headers, data=data)
                print('retrying wow transmission...')
                number_retries += 1
            return str(response.status_code)
        else:
            print('No temperature or payload for transmission...')
            return 'No temperature or payload for transmission...'
    except:
        print("could not connect (status =" + str(wlan.status()) + ")")
        if wlan.status() < 0 or wlan.status() >= 3:
            print("trying to reconnect...")
            wlan.disconnect()
            wlan.connect(ssid, password)
            if wlan.status() == 3:
                print('connected')
                number_retries = 0
                response = requests.post(wow_url, headers=headers, data=data)
                print("sent (" + str(
                    response.status_code) + "), status = " + str(
                    wlan.status()))
                response.close()
                # Retry the wow post if we don't get a 201 response
                while response.status_code != 201 and \
                        number_retries < max_retries:
                    utime.sleep(delay)
                    response = requests.post(wow_url, headers=headers,
                                             data=data)
                    print('retrying wow transmission...')
                    number_retries += 1
                return str(response.status_code)
            else:
                print('failed')
                return 'WoW transmission failed'


def format_time(utime_list):
    """Takes a Micro Python utime list with date/time members and constructs
    into a datetime string format acceptable to the WoW API."""
    formatted_list = []
    for item in utime_list:
        if item < 10:
            formatted_list.append('0' + str(item))
        else:
            formatted_list.append(str(item))
    dtg = formatted_list[0] + '-' + (
        formatted_list[1]) + '-' + (formatted_list[2]) + 'T' + (
              formatted_list[3]) + ':' + (formatted_list[4]) + ':' + (
              formatted_list[5]) + '+' + '00:00'
    return dtg
