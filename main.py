import os
import pandas as pd
import re

def read_file(file_path):
    """ Odczytuje zawartość pliku i zwraca listę linii. """
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.readlines()

def extract_athlete_name(lines):
    """ Wyszukuje imię zawodnika w sekcji # Athlete. """
    athlete_line = next((line for line in lines if "# Athlete" in line), None)
    if athlete_line:
        match = re.search(r'"(\w+)"', athlete_line)
        return match.group(1) if match else "Unknown"
    return "Unknown"

def process_data(file_path, lines):
    """ Przetwarza dane z pliku CSV, oblicza średnie przyspieszenie i przedziały prędkości. """
    header_line = next(i for i, line in enumerate(lines) if "Velocity" in line)
    df = pd.read_csv(file_path, skiprows=header_line, sep=';', decimal=',')

    def compute_future_mean(series, window=7):
        return [series[i:i+window].mean() if i+window <= len(series) else None for i in range(len(series))]

    df['Acceleration_SMA'] = compute_future_mean(df['Acceleration'], window=7)

    max_velocity = df['Velocity'].max()
    bins = list(range(0, int(max_velocity) + 6, 5))
    labels = [f"{bins[i]}-{bins[i+1]}" for i in range(len(bins)-1)]
    df['Velocity_Bin'] = pd.cut(df['Velocity'], bins=bins, labels=labels, right=False)

    def filter_by_time_gap(group):
        selected = []
        top_n = 10
        while len(selected) < 10:
            candidates = group.nlargest(top_n, 'Acceleration_SMA')  
            selected = []
            for _, row in candidates.iterrows():
                if not selected or all(abs(row['Seconds'] - prev['Seconds']) >= 1 for prev in selected):
                    selected.append(row)
                if len(selected) == 10:
                    break
            top_n += 5  
            if top_n > len(group):
                break
        return pd.DataFrame(selected)

    return (
        df.groupby('Velocity_Bin', group_keys=False)
        .apply(filter_by_time_gap)
        .sort_values(by=['Velocity_Bin', 'Seconds'])
        .reset_index(drop=True)[['Timestamp', 'Seconds', 'Velocity', 'Acceleration_SMA', 'Velocity_Bin']]
    )

def save_to_excel(df, athlete_name, file_number, output_folder):
    """ Zapisuje DataFrame do pliku XLSX w podanym folderze. """
    os.makedirs(output_folder, exist_ok=True)  # Tworzy folder, jeśli nie istnieje
    output_file = os.path.join(output_folder, f'wyniki_{athlete_name}_{file_number}.xlsx')
    df.to_excel(output_file, index=False)
    print(f"Zapisano plik: {output_file}")

# Pobranie ścieżki folderu od użytkownika
folder_path = input("Podaj ścieżkę folderu z plikami CSV: ").strip()

# Sprawdzenie, czy folder istnieje
if not os.path.isdir(folder_path):
    print("Podana ścieżka nie istnieje lub nie jest folderem.")
    exit()

# Tworzenie folderu na wyniki wewnątrz podanej ścieżki
output_folder = os.path.join(folder_path, "wyniki")
os.makedirs(output_folder, exist_ok=True)  # Tworzy folder, jeśli nie istnieje

# Pobranie listy plików CSV w folderze
csv_files = [f for f in os.listdir(folder_path) if f.endswith(".csv")]

if not csv_files:
    print("Brak plików CSV w podanym folderze.")
    exit()

all_results = []
# Iteracja po wszystkich plikach CSV i przetwarzanie ich
for file_number, file in enumerate(csv_files, start=1):
    file_path = os.path.join(folder_path, file)
    print(f"Przetwarzanie pliku {file_number}/{len(csv_files)}: {file}")

    # Odczytaj zawartość pliku
    lines = read_file(file_path)

    # Pobierz imię zawodnika
    athlete_name = extract_athlete_name(lines)

    # Przetwórz plik do DataFrame
    df_processed = process_data(file_path, lines)

        # Grupowanie i obliczanie średnich
    df_grouped = (
        df_processed.groupby('Velocity_Bin')
        .agg({'Acceleration_SMA': 'mean'})
        .reset_index()
    )

    # Dodanie wyniku do listy
    all_results.append(df_grouped)

    # Zapisz wynik do Excela w folderze "wyniki"
    save_to_excel(df_processed, athlete_name, file_number, output_folder)

# Łączenie wszystkich wyników w jeden DataFrame
final_df = pd.concat(all_results, ignore_index=True)
final_df=final_df.groupby('Velocity_Bin')['Acceleration_SMA'].mean().reset_index()
# Wyświetlenie lub zapisanie wynikowego DataFrame

output_file = os.path.join(output_folder, f'wyniki_średnie.xlsx')
final_df.to_excel(output_file, index=False)
# final_df.to_csv('path_to_save.csv', index=False)
print("Przetwarzanie wszystkich plików zakończone.")
