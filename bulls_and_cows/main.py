"""
Начнем отгадывать. Первые 4 цифры абсолютно не важны: это могут быть 1234 или 4 рандомных
Собственно пусть в начале спросим 0123.
Пользователь может ответить как угодно (парой б к):
0 0; 0 1; 0 2; 0 3; 0 4; 1 0; 1 1; 1 2; 1 3; 2 0; 2 1; 2 2; 3 0; 4 0 - 14 вариантов
если он отвечает любым из вариантов, то мы отбрасываем множество потенциальных
- то есть нужно составить множество потенциальных вариантов - изначально это все 4 значные
числа с неповторяющимися цифрами, которые могут содержать первым числом ноль
всего вариантов 10 * 9 * 8 * 7 = 5040

пусть вариант 0 0:
тогда мы точно знаем, что можно отбросить все числа, содержащие любую из цифр
останется 6 * 5 * 4 * 3 = 360

пусть вариант 0 1:
мы предположим, что 0 есть в числе. при этом 1 2 3 там нет; 0 точно есть и не на первой позиции
6 * 5 * 4 * 3 = 360 вариантов (0 точно в числе в любой из 3 позиций; и остается 6 чисел по 3 позициям)
360 * 4 = 1440 (но при этом это работает для 4 цифр)

пусть 0 2:
предполагаем, что в числе 0 1: тогда 2,3 там нет, и 0, 1 есть но не на своих позициях
6 * 5 * 7 = 210 (7 вариантов расположить 0 и 1 по своим позициям; при этом остается 6 чисел в 2 п)
210 * 6 = 1260 (6 пар можно взять)

0 3:
логика аналогична для 0 2, видим закономерность:
- нужно посчитать сколькими способами можно выбрать С коров из N позиций, причем чтобы они не стояли
на своих изначальных местах - это можно перебором с помощью функции
- нужно посчитать, сколько остается цифр из А с учетом C коров, и сколькими способами их можно расставить
на N - C позициях
- сколько пар из С коров можно составить

можно все легче, перебором
например, 0123 - 0 1
мб 0123? нет, т.к. коров и быков недостаточно. и так проверяем все числа, обновляя таблицу


теперь перейдем к тому, как же определить, что именно спросить:
для каждого существующего варианта по идее нужно узнать, какие ответы возможны, и сколько после них
останется вариантов. самый перспективный нас и заинтересует
например, после того, как нам ответили на 0123 - 0 1; у нас остается 1440 вариантов
- мы знаем, что если мы спросим снова 0123, то в принципе мы не улучшим ситуацию
- 0124: этот вариант возможен, и он нам может дать следующие ответы
0 0; 0 1; 0 2; 1 0; 1 1
при получении каждого ответа у нас сузится количество возможных ответов
0 0 - 180
0 1 - ... и т.д.
в результате мы смотрим на медианное значение в случае больше 2 возможностей (среднее при 2, 1)
и определяем какое число следующее
- сложность: как определить количество вариантов?
- сложность: 456789 - в данном случае равнозначные цифры, и нет смысла проверять 0125 если 0124 проверено

можно предположить (сходу не знаю так ли это), что при одинаковых возможностях числа равнозначны
(буду отталкиваться от этого предположения пока)

в принципе можно сделать некрасивый дикт с ключами как тапл возможностей, а значения - сет чисел
этот дикт нужно переформировывать при каждом вопросе
кажется не очень дорого, но как забрать возможные ответы...
можно пойти дорогим вариантом, проверяя все ответы, и исключать те, которые оставляют 0 вариантов
(собственно при 0123 - 1 1: уже неприятно определять 0124: 0 1; 0 2; 1 0; 1 1; 1 2; 2 1 - логика
сходу не улавливается; но можно все же в кэше сохранять возможные варианты - их будет становится
же меньше только)
в общем тогда для каждого числа храним список возможных значений
при каждом вопросе проходимся снова по всей таблице, и удаляем лишнее
при этом инициализируем 2 структуры: ключи, которые будем изучать, и таплы из списка значений
если следующее значение из таблицы есть в структуре таплов, то скипаем значение


"""
import logging
import statistics
import string
from typing import Dict, List, Optional, Set, Tuple
import utils

N = 4
ALNUM = tuple(string.digits)
POSSIBLE_ANSWERS = [
    (0, 0),
    (0, 1),
    (0, 2),
    (0, 3),
    (0, 4),
    (1, 0),
    (1, 1),
    (1, 2),
    (1, 3),
    (2, 0),
    (2, 1),
    (2, 2),
    (3, 0),
    (4, 0),
]
logger = logging.getLogger()


def generate_variants(
    current_prefix: str = "", n: int = N, alnum: Tuple[str, ...] = ALNUM
) -> Set[str]:
    result = set()
    stars = current_prefix.count("*")
    for i in alnum:
        if stars and stars == alnum.count("*"):
            continue
        if i not in current_prefix or i == "*":
            if len(current_prefix) < n - 1:
                result.update(generate_variants(current_prefix + i, n, alnum))
            else:
                result.add(current_prefix + i)
    return result


def count_bulls_and_cows(guess: str, answer: str) -> Tuple[int, int]:
    b = c = 0
    for i, char in enumerate(guess):
        if char == answer[i]:
            b += 1
        elif char in answer:
            c += 1
    return b, c


def update_table_after_guess(
    bulls: int, cows: int, guess: str, table: Set[str]
) -> Set[str]:
    new_table = set()
    for variant in table:
        if (bulls, cows) == count_bulls_and_cows(guess, variant):
            new_table.add(variant)
    return new_table


def update_numbers_to_check(
    used_alnum: Tuple[str, ...],
    possible_answers: Dict[str, List[Tuple[int, int]]],
    table: Set[str],
) -> Dict[str, List[int]]:
    result = {}
    not_used_alnum = ALNUM[len(used_alnum) :][:4]
    gen_table = generate_variants(alnum=used_alnum + ("*",) * len(not_used_alnum))
    for number in gen_table:
        not_used_alnum_counter = 0
        new_variant = number
        for i, char in enumerate(number):
            if char == "*":
                new_variant = (
                    new_variant[:i]
                    + not_used_alnum[not_used_alnum_counter]
                    + new_variant[i + 1 :]
                )
                not_used_alnum_counter += 1

        result[new_variant] = []

        new_key_possible_answers = []
        for answer in possible_answers[new_variant]:
            if n := update_table_after_guess(answer[0], answer[1], new_variant, table):
                result[new_variant].append(len(n))
                new_key_possible_answers.append(answer)
        possible_answers[new_variant] = new_key_possible_answers
        if possible_answers[new_variant] == [(4, 0)]:
            return {new_variant: [1]}
    return result


def get_guess(check_these_numbers, questions) -> str:
    best_key, best_median, best_mean = "", float("inf"), float("inf")
    for number, remained_variants in check_these_numbers.items():
        if number in questions:
            continue
        median = statistics.median(remained_variants)
        if median < best_median:
            logger.debug(
                "=> %s %s %s %s",
                number,
                remained_variants,
                median,
                sum(remained_variants),
            )

            best_key, best_median, best_mean = (
                number,
                median,
                statistics.mean(remained_variants),
            )
        elif median == best_median:
            if mean := statistics.mean(remained_variants) < best_mean:
                best_key, best_median, best_mean = number, median, mean
    return best_key


def get_initial_options(first_guess: str = "0123") -> Dict[Tuple[int, int], str]:
    result = {}
    table = generate_variants()
    possible_answers = {number: POSSIBLE_ANSWERS for number in table}
    for answer in POSSIBLE_ANSWERS:
        check_these_numbers = update_numbers_to_check(
            tuple(first_guess), possible_answers, table
        )
        result[answer] = get_guess(check_these_numbers, [])
    return result


def main(
    key: Optional[str] = None,
):
    rounds = 0
    table = generate_variants()
    possible_answers = {number: POSSIBLE_ANSWERS for number in table}
    used_alnum = ("0", "1", "2", "3")
    check_these_numbers = {"0123": [0]}
    questions = set()
    while True:
        rounds += 1
        guess = get_guess(check_these_numbers, questions)
        questions.add(guess)
        used_alnum = tuple(set(used_alnum + tuple(guess)))

        if key:
            inp = " ".join(map(str, count_bulls_and_cows(guess, key)))
            logger.debug("=========================\nguess: %s; b c: %s", guess, inp)
        else:
            print(f'How many bulls and cows in "{guess}"?')
            inp = input("bulls cows: ")
            while tuple(map(int, inp.split())) not in POSSIBLE_ANSWERS:
                print(f"your input is {tuple(inp.split())}")
                inp = input("type correct number of bulls and cows: ")

        bulls, cows = map(int, inp.split())
        if bulls == N:
            logger.debug(f"Won in {rounds}!")
            return rounds
        table = update_table_after_guess(bulls, cows, guess, table)

        check_these_numbers = update_numbers_to_check(
            used_alnum, possible_answers, table
        )


if __name__ == "__main__":
    # utils.init_logger('INFO')
    main("5086")

    # main_table = generate_variants()
    # for i in main_table:
    #     if j := main(i) > 7:
    #         print(f'!!!!!!!!! {j} ', end=' ')
    #     print(i)
