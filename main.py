import os
import csv

cdr_directory = "Синтетические данные (CSV)"
prefixes_file = "Префиксы телефонных номеров (CSV)/PREFIXES.TXT"
output_file = "VOLUMES.TXT"

def compute_prefix_table(pattern):
    prefix_table = [0] * len(pattern)
    length = 0  # длина наибольшего префикса, который является суффиксом

    for i in range(1, len(pattern)):
        while length > 0 and pattern[length] != pattern[i]:
            length = prefix_table[length - 1]

        if pattern[length] == pattern[i]:
            length += 1

        prefix_table[i] = length

    return prefix_table

def kmp_table(pattern):
    m = len(pattern)
    pi = [0] * m
    k = 0
    for q in range(1, m):
        while k > 0 and pattern[k] != pattern[q]:
            k = pi[k - 1]
        if pattern[k] == pattern[q]:
            k += 1
        pi[q] = k
    return pi

def kmp_search(text, pattern):
    matches = []
    if not pattern:
        return matches

    prefix_table = compute_prefix_table(pattern)
    q = 0  # индекс символа в образце

    for i in range(len(text)):
        while q > 0 and pattern[q] != text[i]:
            q = prefix_table[q - 1]

        if pattern[q] == text[i]:
            q += 1

        if q == len(pattern):
            matches.append(i - len(pattern) + 1)
            q = prefix_table[q - 1]

    return matches

# Загрузка префиксов из файла PREFIXES.TXT
prefixes = {}

with open(prefixes_file, "r") as file:
    reader = csv.reader(file, delimiter=",")
    for row in reader:
        zone = row[0]
        prefixes_list = row[1:]

        if zone in prefixes:
            # Если префиксная зона уже существует, добавляем новые префиксы к списку
            existing_prefixes = prefixes[zone]
            existing_prefixes.extend(prefixes_list)
            prefixes[zone] = existing_prefixes
        else:
            # Если префиксная зона новая, создаем новую запись
            prefixes[zone] = prefixes_list

# Инициализация словаря для хранения статистики длительности соединений
volume_stats = {}

# Обработка CDR файлов
for filename in os.listdir(cdr_directory):
    if filename.endswith(".TXT"):
        cdr_file = os.path.join(cdr_directory, filename)

        # Чтение CDR файла
        with open(cdr_file, "r") as file:
            reader = csv.reader(file, delimiter=",")
            cdr_rows = list(reader)

        # Обработка каждой записи в CDR файле
        for row in cdr_rows:
            msisdn = row[5]
            dialed = row[6]

            msisdn_zone = "Unknown"
            dialed_zone = "Unknown"

            # Поиск префиксной зоны для MSISDN и DIALED
            for zone, prefixes_list in prefixes.items():
                prefixes_str = "|".join(prefixes_list)

                # Поиск префиксной зоны для MSISDN
                matches = kmp_search(msisdn, prefixes_str)
                if matches:
                    longest_match_index = max(matches, key=lambda x: len(msisdn[x:x + len(prefixes_str)]))
                    longest_match = msisdn[longest_match_index:longest_match_index + len(prefixes_str)]
                    msisdn_zone = zone
                    break

                # Поиск префиксной зоны для DIALED
                matches = kmp_search(dialed, prefixes_str)
                if matches:
                    longest_match_index = max(matches, key=lambda x: len(dialed[x:x + len(prefixes_str)]))
                    longest_match = dialed[longest_match_index:longest_match_index + len(prefixes_str)]
                    dialed_zone = zone
                    break

            # Запись префиксных зон в поля №10 и №11
            row[9] = msisdn_zone
            row[10] = dialed_zone

            # Обновление статистики длительности соединений
            key = (msisdn_zone, dialed_zone)
            duration = int(row[8])
            volume_stats[key] = volume_stats.get(key, 0) + duration

        # Сохранение обновленного CDR файла
        with open(cdr_file, "w", newline="") as file:
            writer = csv.writer(file, delimiter=",")
            writer.writerows(cdr_rows)

# Запись статистики длительности соединений в файл VOLUMES.TXT
with open(output_file, "w", newline="") as file:
    writer = csv.writer(file, delimiter=",")
    writer.writerow(["Prefix_Zone_MSISDN", "Prefix_Zone_DIALED", "Total_Duration"])
    for key, duration in volume_stats.items():
        writer.writerow([key[0], key[1], duration])