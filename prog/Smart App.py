import smartapp_api
import weerapp
import smartapp_controler

def main():
    keuze = 0
    print('welkom in SunnySide, de zon schijnt altijd ergens!')
    while True:
        print('=============================================================================================')
        print('1 Weer-app')
        print('2 Smart app controller')
        print('3 Smart app API')
        print('4 stoppen')
        try:
            keuze = int(input('Wat wil je doen: '))
            if keuze == 1:
                print('=============================================================================================')
                weerapp.main()
            elif keuze == 2:
                print('=============================================================================================')
                smartapp_controler.main()
            elif keuze == 3:
                smartapp_api.main()
            elif keuze == 4:
                print('=============================================================================================')
                print('Tot de volgende keer')
                break
            else:
                print('Voer een getal van 1 tot 4')
        except ValueError:
            print('Voer en getal van 1 tot 4')

if __name__ == '__main__':
    main()