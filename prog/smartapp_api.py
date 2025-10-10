def main():

    import openmeteo_requests

    openmeteo = openmeteo_requests.Client()

    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": 52.0907,
        "longitude": 05.1214,
        "hourly": "temperature_2m",
        "current": "temperature_2m",

    }
    responses = openmeteo.weather_api(url, params=params)


    response = responses[0]

    current = response.Current()
    current_temperature_2m = current.Variables(0).Value()

    current_temperature_2m = round(current_temperature_2m, 1)

    print('=============================================================================================')
    print(f"Huidige temparatuur Utrecht: {current_temperature_2m}")
if __name__ == '__main__':
    main()