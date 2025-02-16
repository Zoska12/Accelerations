import os
import pandas as pd
import re
import numpy as np

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

def extract_athlete_name(lines):
        # Odczytanie daty eksportu (pierwszy wiersz) i usunięcie godziny
    # Odczytanie nazwy atlety (siódmy wiersz) i usunięcie zbędnych średników
    athlete_name = lines[7].split(":")[1].strip().replace('"', '').split(";")[0]
    if athlete_name:
        return athlete_name
    return "Unknown_name"


def extract_date(lines):
         # Odczytanie daty eksportu (pierwszy wiersz) i usunięcie godziny
    export_date = " ".join(lines[1].split(":")[1].strip().split()[:1])  # Pobiera tylko część z datą
    if export_date:
        return export_date
    return "Unknown_date"

def process_file(file_path, lines):

    """ Przetwarza dane z pliku CSV, oblicza średnie przyspieszenie i przedziały prędkości. """
    header_line = next(i for i, line in enumerate(lines) if "Velocity" in line)
    df = pd.read_csv(file_path, skiprows=header_line, sep=';', decimal=',')

    def compute_future_mean(series, window=7):
        return [series[i:i+window].mean() if i+window <= len(series) else None for i in range(len(series))]

    df['Acceleration_SMA'] = compute_future_mean(df['Acceleration'], window=7)

    return df

def process_data(df, start_date=None,end_date=None):
    # Zamiana pustych wartości na NaN, jeśli są
    #df['Timestamp'] = df['Timestamp'].replace("", np.nan)
    # Konwersja do datetime z obsługą błędów
    #df['Timestamp'] = pd.to_datetime(df['Timestamp'], format="%d.%m.%Y %H:%M", errors='coerce')

    df['Timestamp'] = pd.to_datetime(df['Timestamp'], errors='coerce', dayfirst=True)
    # Konwersja Timestamp do HH:MM bez sekund
    df['Timestamp_time'] = df['Timestamp'].dt.strftime('%H:%M')

    if start_date is not None and end_date is not None:
        # Konwersja start_date i end_date na ten sam format HH:MM (bez sekund)
        start_time = pd.to_datetime(start_date, format='%H:%M').strftime('%H:%M')
        end_time = pd.to_datetime(end_date, format='%H:%M').strftime('%H:%M')

        # Filtrowanie danych na podstawie godzin
        df = df[(df['Timestamp_time'] >= start_time) & (df['Timestamp_time'] <= end_time)]


    bins = [5, 10, 15]  # Dwa przedziały: 5-10 i 10-15
    labels = ["5-10", "10-15"]
    df['Velocity_Bin'] = pd.cut(df['Velocity'], bins=bins, labels=labels, right=False)

    def filter_by_time_gap(group):

        if group.empty:
            return pd.DataFrame({
                'Timestamp': [np.nan], 
                'Seconds': [np.nan], 
                'Velocity': [np.nan], 
                'Acceleration_SMA': [np.nan], 
                'Velocity_Bin': [group.name]  # Przypisanie pustej grupy do Velocity_Bin
            })
        selected = []
        #top_n = 10
        top_n = 3
        while len(selected) < 3:
            candidates = group.nlargest(top_n, 'Acceleration_SMA')  
            selected = []
            for _, row in candidates.iterrows():
                if not selected or all(abs(row['Seconds'] - prev['Seconds']) >= 1 for prev in selected):
                    selected.append(row)
                if len(selected) == 3:
                    break
            #top_n += 5
            top_n += 3  
            if top_n > len(group):
                break
        return pd.DataFrame(selected)

    return (
        df.groupby('Velocity_Bin', group_keys=False)
        .apply(filter_by_time_gap)
        .sort_values(by=['Velocity_Bin', 'Seconds'])
        .reset_index(drop=True)[['Timestamp', 'Seconds', 'Velocity', 'Acceleration_SMA', 'Velocity_Bin']]
    )


def save_to_excel(df, athlete_name, date, file_number, output_folder):
    """ Zapisuje DataFrame do pliku XLSX w podanym folderze. """
    os.makedirs(output_folder, exist_ok=True)  # Tworzy folder, jeśli nie istnieje
    #print(type(df['Timestamp'].iloc[0]))
    df['Timestamp'] = df['Timestamp'].fillna(pd.to_datetime(date, format='%d.%m.%Y'))
    output_file = os.path.join(output_folder, f'wyniki_{athlete_name}_{date}_{file_number}.xlsx')
    df.to_excel(output_file, index=False)
    print(f"Zapisano plik: {output_file}")

# Pobranie ścieżki folderu od użytkownika
#folder_path = input("Podaj ścieżkę folderu z plikami CSV: ").strip()

#TU WPISZ ŚCIEŻKĘ 
folder_path = "Przykladowy Folder"
folder_path = "Raw files GPS/Raw files GPS Zagłębie/czwartek"
#folder_path = "Raw files GPS/Raw files GPS Zagłębie/środa"
#folder_path = "Raw files GPS/Raw files GPS Zagłębie/wtorek"
#folder_path = "Raw files GPS/Raw files GPS Zagłębie/poniedziałek"

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
    date = extract_date(lines)
    # Przetwórz plik do DataFrame
    
    df = process_file(file_path, lines)
    
    #TU PODAJ ZAKRES CZASU I TYP ĆWICZENIA DLADANEGO TRENINGU (folderu który przetwarzasz)
    #podzial = {'Duża Gra':["14:10","14:15"], 'Mała Gra':["14:16","14:30"]}

    #podzial = {'Duża Gra':["11:15","11:30"], 'Mała Gra':["11:31","12:00"]}
    #JEŚLI WPISZESZ PUSTE NAWIASY [] TO WEŹMIE CAŁY PLIK  
    podzial = {'Gra':[]}
    results=[]

    for key, value in podzial.items():


        start_time = value[0] if len(value) > 0 and value[0] else None
        end_time = value[1] if len(value) > 1 and value[1] else None

        df_processed = process_data(df, start_time, end_time)

        df_processed['Trening']=key
            # Grupowanie i obliczanie średnich
        df_grouped = (
        df_processed.groupby(['Velocity_Bin', 'Trening'])
        .agg({'Acceleration_SMA': 'mean'})
        .reset_index()
        )


        results.append(df_processed)

    final_results = pd.concat(results, ignore_index=True)    
    # Dodanie wyniku do listy
    all_results.append(final_results)


    # Zapisz wynik do Excela w folderze "wyniki"
    save_to_excel(final_results, athlete_name,date, file_number, output_folder)
 

# Łączenie wszystkich wyników w jeden DataFrame
final_df = pd.concat(all_results, ignore_index=True)

if not final_df.empty:
    final_df = final_df.groupby(['Velocity_Bin', 'Trening'], observed=False)['Acceleration_SMA'].mean().reset_index()
else:
    final_df = pd.DataFrame(columns=['Velocity_Bin', 'Trening', 'Acceleration_SMA'])

# Wyświetlenie lub zapisanie wynikowego DataFrameS

output_file = os.path.join(output_folder, f'wyniki_średnie.xlsx')
final_df.to_excel(output_file, index=False)
# final_df.to_csv('path_to_save.csv', index=False)
print("Przetwarzanie wszystkich plików zakończone.")
