temparaturen = []
no_input = 'Geen input gegeven'
def fahrenheit(temp_celcius):
    """
    berekend de warmte in fahrenheit
    :param temp_celcius: de warmte in graden celcius
    :return: de warmte in graden fahrenheit
    """
    fheit = 32 + 1.8 * temp_celcius
    return fheit
def gevoelstemperatuur(temp_celcius, windsnelheid, luchtvochtigheid):
    """
    berekend de gevoels temparatuur
    :param temp_celcius: de temparatuur in graden celcius
    :param windsnelheid: de windsnelheid in m/s
    :param luchtvochtigheid: de luchtvochtigheid in gehelde procenten
    :return: geeft de gevoels temparatuur
    """
    gevoel_temp = temp_celcius - (luchtvochtigheid / 100 * windsnelheid)
    return gevoel_temp
def weerrapport(temp_celcius, windsnelheid, luchtvochtigheid):
    """
    laat de temparatuur zien, geeft een string gebaseerd op de gevoels temparatuur en berekend de gemiddelde temparatuur in graden celcius

    """
    print('Het is', str(temp_celcius) +  'C', '(' + str(fahrenheit(temp_celcius)) + 'F)')
    gevoel_temp = gevoelstemperatuur(temp_celcius, windsnelheid, luchtvochtigheid)
    if gevoel_temp < 0 and windsnelheid > 10:
        print('Het is heel koud en het stormt! Verwarming helemaal aan!')
    elif gevoel_temp < 0 and windsnelheid <= 10:
        print('Het is behoorlijk koud! Verwarming aan op de benedenverdieping!')
    elif 0 <= gevoel_temp < 10 and windsnelheid > 12:
        print('Het is best koud en het waait; verwarming aan en roosters dicht!')
    elif 0 <= gevoel_temp < 10 and windsnelheid <= 12:
        print('Het is een beetje koud, elektrische kachel op de benedenverdieping aan!')
    elif 10 <= gevoel_temp < 22 and windsnelheid:
        print('Heerlijk weer, niet te koud of te warm.')
    else:
        print('Warm! Airco aan!')
    temparaturen.append(temp_celcius)
    print('Gem. temp tot nu toe is', str(sum(temparaturen)/len(temparaturen)))
    print('=============================================================================================')
def main():
    celcius_1 = (input('Wat is op dag 1 de temperatuur[C]: '))
    if len(celcius_1) == 0:
        print(no_input)
        return 'geen input gegeven'
    snelheid_1 = (input('Wat is op dag 1 de windsnelheid[m/s]: '))
    if len(snelheid_1) == 0:
        print(no_input)
        return 'geen input gegeven'
    procent_1 = (input('Wat is op dag 1 de vochtigheid[%]: '))
    if len(procent_1) == 0:
        print(no_input)
        return 'geen input gegeven'
    weerrapport(float(celcius_1), float(snelheid_1), int(procent_1))
    celcius_2 = (input('Wat is op dag 2 de temperatuur[C]: '))
    if len(celcius_2) == 0:
        print(no_input)
        return 'geen input gegeven'
    snelheid_2 = (input('Wat is op dag 2 de windsnelheid[m/s]: '))
    if len(snelheid_2) == 0:
        print(no_input)
        return 'geen input gegeven'
    procent_2 = (input('Wat is op dag 2 de vochtigheid[%]: '))
    if len(procent_2) == 0:
        print(no_input)
        return 'geen input gegeven'
    weerrapport(float(celcius_2), float(snelheid_2), int(procent_2))
    celcius_3 = (input('Wat is op dag 3 de temperatuur[C]: '))
    if len(celcius_3) == 0:
        print(no_input)
        return 'geen input gegeven'
    snelheid_3 = (input('Wat is op dag 3 de windsnelheid[m/s]: '))
    if len(snelheid_3) == 0:
        print(no_input)
        return 'geen input gegeven'
    procent_3 = (input('Wat is op dag 3 de vochtigheid[%]: '))
    if len(procent_3) == 0:
        print(no_input)
        return 'geen input gegeven'
    weerrapport(float(celcius_3), float(snelheid_3), int(procent_3))
if __name__ == '__main__':
    main()