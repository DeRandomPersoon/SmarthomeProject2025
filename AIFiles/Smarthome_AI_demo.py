import csv
import algroritmes as al
import matplotlib.pyplot as plt
import openmeteo_requests
import schedule
import time
import pandas as pd
import requests_cache
from retry_requests import retry

file = open('panelen_data_extra.csv')
reader = csv.DictReader(file)
headers = reader.fieldnames
data = {}
for header in headers:
    data[header] = []
for row in reader:
    row['id'] = int(row['id'])
    row['KiloWattDag'] = float(row['KiloWattDag'])
    row['Gem%BewolkingDag'] = float(row['Gem%BewolkingDag'])
    row['GemTempDag'] = float(row['GemTempDag'])
    row['LuxDag'] = int(row['LuxDag'])
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
    gem_temp = -1
    lux_dag = -1
    id = len(data['id'])
    bewolking_data = openmateo_api()
    gradient_descent = al.gradient_descent(data['Gem%BewolkingDag'], data['KiloWattDag'], 100000, 0.0001)
    a = gradient_descent[0]
    b = gradient_descent[1]
    voorspelde_kilowatt = a + b * bewolking_data[1]
    file = open('panelen_data_extra.csv', 'a')
    file.write(f'{id},{werkelijke_opbrengst_van_gister},{bewolking_data[0]},{gem_temp},{lux_dag}\n')
    file.close()
    data['Gem%BewolkingDag'].append(bewolking_data[0])
    data['KiloWattDag'].append(werkelijke_opbrengst_van_gister)
    data['GemTempDag'].append(gem_temp)
    data['LuxDag'].append(lux_dag)
    data['id'].append(id + 1)
    print(voorspelde_kilowatt)
    return voorspelde_kilowatt


gradient_descent = al.gradient_descent(data['Gem%BewolkingDag'], data['KiloWattDag'], 100000, 0.0001)
a = gradient_descent[0]
b = gradient_descent[1]
print(a)
print(b)
voorspelde_kilowatt_1 = a + b * 0
voorspelde_kilowatt_2 = a + b * 100

x = data['Gem%BewolkingDag']
y = data['KiloWattDag']
plt.scatter(x, y)
x = [0, 100]
y = [voorspelde_kilowatt_1, voorspelde_kilowatt_2]
plt.plot(x, y, c = 'y')
plt.title('Zonnepanelen Opbrengst in Kilo Watt')
plt.xlabel('Gemiddelde % Bewolking Dag')
plt.ylabel('Energie in Kilo Watt')
plt.xlim(0, 100)
plt.ylim(0, 10)
plt.grid()
plt.show()

schedule.every(5).seconds.do(job)
while True:
    schedule.run_pending()
    time.sleep(1)