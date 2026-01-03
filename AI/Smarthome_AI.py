import csv
import algroritmes as al
import openmeteo_requests
import schedule
import time
import pandas as pd
import requests_cache
from retry_requests import retry

file = open('panelen_data.csv')
reader = csv.DictReader(file)
headers = reader.fieldnames
data = {}
for header in headers:
    data[header] = []
for row in reader:
    row['KiloWattDag'] = float(row['KiloWattDag'])
    row['Gem%BewolkingDag'] = float(row['Gem%BewolkingDag'])
    for header in headers:
        data[header].append(row[header])

def openmateo_api():
    """
    code van open mateo api
    return: de gemiddelde % bewolking van de dag
    """
    cache_session = requests_cache.CachedSession('.cache', expire_after = 3600)
    retry_session = retry(cache_session, retries = 5, backoff_factor = 0.2)
    openmeteo = openmeteo_requests.Client(session = retry_session)


    url = "https://api.open-meteo.com/v1/forecast?latitude=52.52&longitude=13.41&hourly=cloud_cover&past_days=1&forecast_days=1"
    params = {
        "latitude": 52.0386111,
        "longitude": 5.066666666666666,
        "hourly": "cloud_cover",
        "forecast_days": 1,
    }
    responses = openmeteo.weather_api(url, params=params)

    response = responses[0]

    hourly = response.Hourly()
    hourly_cloud_cover = hourly.Variables(0).ValuesAsNumpy()

    hourly_data = {"date": pd.date_range(
        start = pd.to_datetime(hourly.Time(), unit = "s", utc = True),
        end =  pd.to_datetime(hourly.TimeEnd(), unit = "s", utc = True),
        freq = pd.Timedelta(seconds = hourly.Interval()),
        inclusive = "left"
    )}

    hourly_data["cloud_cover"] = hourly_cloud_cover

    bewolking_data = [float(sum(hourly_cloud_cover[23:])) / 24, float(sum(hourly_cloud_cover[:24]) / 24)]
    return bewolking_data

def job():
    werkelijke_opbrengst_van_gister = -1
    bewolking_data = openmateo_api()
    gradient_descent = al.gradient_descent(data['Gem%BewolkingDag'], data['KiloWattDag'], 100000, 0.0001)
    a = gradient_descent[0]
    b = gradient_descent[1]
    voorspelde_kilowatt = a + b * bewolking_data[1]
    file = open('panelen_data.csv', 'a')
    file.write(f'{werkelijke_opbrengst_van_gister},{bewolking_data[0]}\n')
    file.close()
    data['Gem%BewolkingDag'].append(bewolking_data[0])
    data['KiloWattDag'].append(werkelijke_opbrengst_van_gister)
    return voorspelde_kilowatt

schedule.every().day.at('00:00').do(job)
while True:
    schedule.run_pending()
    time.sleep(1)


