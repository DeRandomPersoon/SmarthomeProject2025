def binair_zoeken(lst, target):
    mini = 0
    maxi = len(lst) - 1

    while mini <= maxi:
        index = (mini + maxi) // 2
        if lst[index] == target:
            return index
        if lst[index] < target:
            mini = index + 1
        else: #lst[index] > target:
            maxi = index -1
    return -1

def modus_zoeken(lst):
    nummers = []
    counters = []
    for nummer in lst:
        lst_counter = 0
        counter = 0
        if nummer not in nummers:
            nummers.append(nummer)
            for nummer_match in lst:
                if nummer == nummer_match:
                    counter = counter + 1
                lst_counter = lst_counter + 1
                if lst_counter == len(lst):
                    counters.append(counter)
    max_counters = max(counters)
    if max_counters == 1:
        return 'Er is geen modus'
    indexen = []
    index = 0
    for counter in counters:
        if counter == max_counters:
            indexen.append(index)
            index += 1
        else:
            index += 1
    modussen = []
    for i in indexen:
        modussen.append(nummers[i])
    return modussen

def mediaan_berekenen(lst):
    opdeling = len(lst) % 2
    helft = len(lst) // 2
    if opdeling == 0:
        mediaan = (lst[helft - 1] + lst[helft]) / 2
    else:
        mediaan = lst[int(helft)]
    return mediaan

def gemiddelde_berekenen(lst):
    return sum(lst) / len(lst)

def range_lijst(lst):
    return max(lst) - min(lst)

def variantie(lst):
    gemiddelde = gemiddelde_berekenen(lst)
    gekwadrateerde_verschillen =[]
    for getal in lst:
        gekwadrateerde_verschillen.append((gemiddelde - getal)**2)
    return sum(gekwadrateerde_verschillen) / len(lst)

def interkwartielafstand(lst):
    opdeling = len(lst) % 2
    helft = len(lst) // 2
    if opdeling == 0:
        boven_mediaan = lst[helft:]
        onder_mediaan = lst[:helft]
    else:
        boven_mediaan = lst[helft + 1:]
        onder_mediaan = lst[:helft]
    Q3 = mediaan_berekenen(boven_mediaan)
    Q1 = mediaan_berekenen(onder_mediaan)
    return Q3 -Q1

def uitschieters_berekenen(lst):
    IQR = interkwartielafstand(lst)
    opdeling = len(lst) % 2
    helft = len(lst) // 2
    if opdeling == 0:
        boven_mediaan = lst[helft:]
        onder_mediaan = lst[:helft]
    else:
        boven_mediaan = lst[helft + 1:]
        onder_mediaan = lst[:helft]
    Q3 = mediaan_berekenen(boven_mediaan)
    Q1 = mediaan_berekenen(onder_mediaan)
    onder_grens =  Q1 - (1.5 * IQR)
    boven_grens = Q3 + (1.5 * IQR)
    uitschieters = []
    for getal in lst:
        if getal < onder_grens:
            uitschieters.append(getal)
        if getal > boven_grens:
            uitschieters.append(getal)
    if len(uitschieters) == 0:
        return 'Er zijn geen uitschieters'
    else:
        return uitschieters


def selection_sort(lst):
    index = 0
    min_index = 0
    while index != len(lst) -1:
        min = lst[index]
        vergelijk = index + 1
        while vergelijk != len(lst):
            if min < lst[vergelijk]:
                vergelijk =vergelijk + 1
            else: # min > lst[vergelijk]
                min = lst[vergelijk]
                min_index = vergelijk
                vergelijk = vergelijk + 1
        if min != lst[index]:
            lst[min_index] = lst[index]
            lst[index] = min
        index = index + 1
    return lst
def corrolatie_berekenen(lst_1, lst_2):
    teller = 0
    x_1_kwadraat = 0
    y_1_kwadraat = 0
    gem_x = mediaan_berekenen(lst_1)
    gem_y = mediaan_berekenen(lst_2)
    n = len(lst_1)
    for i in range(n):
        x_1 = lst_1[i] - gem_x
        y_1 = lst_2[i] - gem_y
        teller += x_1 * y_1
        x_1_kwadraat += x_1 ** 2
        y_1_kwadraat += y_1 ** 2
    noemer = (x_1_kwadraat * y_1_kwadraat) ** 0.5
    if noemer == 0 or teller == 0:
        return 0.0
    else:
        correlatie = teller / noemer
        return correlatie
def gradient_descent(x, y, num_iterations=10000, learning_rate=0.0001):
    """
    Traint de coefficienten a en b voor het lineaire regressiemodel ŷ = a + b * x met de gradient descent methode.

    Args:
        x (list): de onafhankelijke waarden van de observaties
        y (list): de afhankelijke waarden van de observaties
        num_iterations (int): aantal iteraties om te leren
        learning_rate (float): leerconstante

    Returns:
        [float, float]: de berekende coefficienten
    """
    n = len(x)
    iterations = 0
    a = 0
    b = 0
    while True:
        if iterations != num_iterations:
            grad_a = 0
            grad_b = 0
            for i in range(n):
                error = (a + b * x[i]) - y[i]
                grad_a = grad_a + (2 * error)
                grad_b = grad_b + (2 * error * x[i])
            a = a - grad_a * learning_rate / n
            b = b - grad_b * learning_rate / n
            iterations = iterations + 1
        else:
            coefficients = [a, b]
            return coefficients
