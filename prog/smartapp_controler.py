
inputFile = 'smartapp_input.txt'
outputFile = 'smartapp_output.txt'

def aantal_dagen(inputFile):
    """
    Geeft de aantal dagen die in inputFile staan
    """
    file = open(inputFile, 'r')
    next(file)
    regels = file.readlines()
    file.close()
    return len(regels)

def auto_bereken(inputFile, outputFile):
    """
    Berekend welke waardes worden gebruikt voor de CV ketel, ventilatie en het bewatering systeem
    :param inputFile: de file met de info voor de berekeningen
    :param outputFile: de file waar de resultaten in worden opgeslagen
    :return: niks het bewerkt de output file aleen
    """
    file_input = open(inputFile, 'r')
    next(file_input)
    regels = file_input.readlines()
    file_output = open(outputFile, 'w')
    for regel in regels:
        output_list = []
        waardes = regel.strip().split()
        output_list.append(waardes[0])
        verschil_temp = abs(float(waardes[2]) - float(waardes[3]))
        if verschil_temp >= 20:
            cv_procent = '100'
        elif 20 > verschil_temp >= 10:
            cv_procent = '50'
        elif verschil_temp < 10:
            cv_procent = '0'
        else:
            cv_procent = '-1'
        output_list.append(cv_procent)
        ventilatie_stand = int(waardes[1]) + 1
        if ventilatie_stand > 4:
                ventilatie_stand = 4
        output_list.append(str(ventilatie_stand))
        regen_mm = int(waardes[4])
        if regen_mm < 3:
            bewatering = 'True'
        else:
            bewatering = 'False'
        output_list.append(bewatering)
        output = ';'.join(output_list)
        file_output.write(output)
        file_output.write('\n')
    file_output.close()

def overwrite_settings(outputFile):
    """
    Laat je bepaalde waardes in de output file veranderen
    """
    return_waarde = '0'
    file = open(outputFile, 'r')
    regels = file.readlines()
    file.close()
    datum = input('Bij welke datum wilt u iets veranderen (dd-mm-jjjj): ')
    teller = 0
    if len(datum) == 10:
        for regel in regels:
            if datum in regel:
                print('1 CV-ketel')
                print('2 Ventilatie')
                print('3 Bewatering')
                keuze = input(f'Wat wilt u veranderen op {datum}: ')
                waardes = regel.strip().split(';')
                if keuze == '1':
                    cv_sterkte = input('Hoe hard wilt u de CV-ketel zetten (0-100): ')
                    try:
                        if 0 <= int(cv_sterkte) <= 100:
                            waardes[1] = str(cv_sterkte)
                            update = ';'.join(waardes)
                            regels[teller] = update + '\n'
                            file_edit = open(outputFile, 'w')
                            file_edit.writelines(regels)
                            file_edit.close()
                            return_waarde = '0'
                            break
                    except ValueError:
                        return_waarde = '-3'
                        break
                    else:
                        return_waarde = '-3'
                        break
                elif keuze == '2':
                    vent_sterkte = (input('Hoe hard wilt u de ventilatie zetten (0-4): '))
                    try:
                        if 0 <= int(vent_sterkte) <= 4:
                            waardes[2] = str(vent_sterkte)
                            update = ';'.join(waardes)
                            regels[teller] = update + '\n'
                            file_edit = open(outputFile, 'w')
                            file_edit.writelines(regels)
                            file_edit.close()
                            return_waarde = '0'
                            break
                        else:
                            return_waarde = '-3'
                            break
                    except ValueError:
                        return_waarde = '-3'
                        break
                elif keuze == '3':
                    bewatering = input('wilt u de bewatering uit of aan zetten (0/1): ')
                    if bewatering == '0':
                        waardes[3] = 'False'
                        update = ';'.join(waardes)
                        regels[teller] = update + '\n'
                        file_edit = open(outputFile, 'w')
                        file_edit.writelines(regels)
                        file_edit.close()
                        return_waarde = '0'
                        break
                    elif bewatering == '1':
                        waardes[3] = 'True'
                        update = ';'.join(waardes)
                        regels[teller] = update + '\n'
                        file_edit = open(outputFile, 'w')
                        file_edit.writelines(regels)
                        file_edit.close()
                        return_waarde = '0'
                        break
                    else:
                        return_waarde = '-3'
                        break
                else:
                    return_waarde = '-3'
            else:
                teller = teller + 1
                if teller == len(regels) - 1:
                    return_waarde = '-3'
    else:
        return_waarde = '-1'
    return return_waarde

def main():
    print('Welkom in de smart app controler')
    while True:
        print('1 Aantal dagen weergeven')
        print('2 Automatisch berekenen (Let op, wijzigingen worden ongedaan!)')
        print('3 Waarde overschrijven in het uitvoerbestand')
        print('4 Stoppen')
        keuze = input('Wat wilt u doen: ')
        if keuze == '1':
            print('=============================================================================================')
            print(f'U heeft info van {aantal_dagen(inputFile)} dagen')
            print('=============================================================================================')

        elif keuze == '2':
            print('=============================================================================================')
            auto_bereken(inputFile, outputFile)
            print('Alles is automatisch berekend')
            print('=============================================================================================')

        elif keuze == '3':
            print('=============================================================================================')
            print(overwrite_settings(outputFile))
            print('=============================================================================================')

        elif keuze == '4':
            break

        else:
            print('Voer een nummer van 1-4')
            print('=============================================================================================')
if __name__ == '__main__':
    main()