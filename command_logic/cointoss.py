from random import randint


def coin_toss():
    random = randint(1, 101)

    if random < 51: return 'Kopf'
    elif random == 101: return 'Kante'
    else: return 'Zahl'
