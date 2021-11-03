"""
1) Составляем таблицу возможных значений на основании ответов пользователя
2) С учетом первого ответа пользователя, обновляем таблицу возможных значений 1
3) Для каждого числа из ВСЕХ значений проверяем все возможные ответы пользователя,
и выбираем то число, которое при любом ответе будет максимально уменьшать таблицу 1
- оптимизация 1: запоминаем для каждого числа список возможных ответов, уменьшая его на каждой итерации
- оптимизация 2: цифры, которые еще не спрашивались - равнозначны. варианты с ними схлопываются
4) повторяем 2-3, пока пользователь не напишет 0 4 или в таблице 1 останется одно число
"""
import logging
import string
from typing import Any, Dict, List, Optional, Set, Tuple
import utils

N = 4
ALNUM = tuple(string.digits)
POSSIBLE_ANSWERS = {
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
}
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
    bulls: int, cows: int, guess: str, table: List[str]
) -> List[str]:
    new_table = []
    for variant in table:
        if (bulls, cows) == count_bulls_and_cows(guess, variant):
            new_table.append(variant)
    return new_table


def update_numbers_to_check(
    used_alnum: Tuple[str, ...],
    possible_answers: Dict[str, List[Tuple[int, int]]],
    table: List[str],
) -> Dict[str, List[int]]:
    result = {}
    not_used_alnum = ALNUM[len(used_alnum) :][:4]
    gen_table = sorted(
        generate_variants(alnum=used_alnum + ("*",) * len(not_used_alnum))
    )
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
    return result


def get_guess(check_these_numbers: dict, possible_answers: dict) -> str:
    best_guess, best_val = "", float("inf")
    for number, remained_variants in check_these_numbers.items():
        max_val = max(remained_variants)
        if max_val < best_val or (
            max_val == best_val and (4, 0) in possible_answers[number]
        ):
            best_guess, best_val = number, max_val
    return best_guess


def get_initial_options(guess: str = "0123") -> Any:
    result = {}
    table = sorted(generate_variants())
    for answer in POSSIBLE_ANSWERS:
        changed_table = update_table_after_guess(answer[0], answer[1], guess, table)
        check_these_numbers = update_numbers_to_check(
            tuple(guess), {number: POSSIBLE_ANSWERS for number in table}, changed_table
        )
        result[answer] = changed_table, check_these_numbers
    return result


def get_input(key: str, guess: str, table: List[str]) -> Any:
    if key:
        inp = " ".join(map(str, count_bulls_and_cows(guess, key)))
        logger.debug(
            "=> guess: %s; b c: %s; len: %s\n",
            guess,
            inp,
            len(table),
        )
    else:
        print(f'How many bulls and cows in "{guess}"?')
        inp = input("bulls cows: ")
        while True:
            try:
                if tuple(map(str, inp.split())) in POSSIBLE_ANSWERS:
                    break
            except:
                pass
            inp = input("type correct number of bulls and cows: ")

    return map(int, inp.split())


def main(key: Optional[str] = None) -> int:
    rounds = 0
    table = sorted(generate_variants())
    possible_answers = {number: POSSIBLE_ANSWERS for number in table}
    used_alnum = ("0", "1", "2", "3")
    check_these_numbers = {"0123": [0]}
    while True:
        rounds += 1
        guess = get_guess(check_these_numbers, possible_answers)
        if len(used_alnum) < 8:
            used_alnum = tuple(set(used_alnum + tuple(guess)))
        else:
            used_alnum = ALNUM

        while True:
            bulls, cows = get_input(key, guess, table)
            table = update_table_after_guess(bulls, cows, guess, table)
            if table:
                break
            print("Enter valid answer.")
        if bulls == 4 or len(table) == 1:
            rounds += bulls != 4
            logger.debug(f"Your num is {table.pop()}. Won in {rounds} rounds!")
            return rounds

        check_these_numbers = update_numbers_to_check(
            used_alnum, possible_answers, table
        )


if __name__ == "__main__":
    main()
