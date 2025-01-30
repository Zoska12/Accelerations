import os
import pandas as pd

# Ścieżka do katalogu, w którym znajdują się foldery dni tygodnia
base_path = "Raw files GPS\Raw files GPS Zagłębie"  # <-- Zmień na właściwą ścieżkę

# Tworzenie słownika, w którym będą przechowywane dane dla każdego piłkarza
players_data = {}

# Iteracja po folderach w bazowej lokalizacji
for folder_name in os.listdir(base_path):
    folder_path = os.path.join(base_path, folder_name)

    # Sprawdzenie, czy to folder
    if not os.path.isdir(folder_path):
        continue

    # Sprawdzenie, czy folder zawiera podfolder "wyniki"
    results_path = os.path.join(folder_path, "wyniki")
    if not os.path.exists(results_path):
        continue

    # Iteracja po plikach Excela w folderze "wyniki"
    for file_name in os.listdir(results_path):
        if file_name.endswith(".xlsx"):
            file_path = os.path.join(results_path, file_name)

            # Wydobycie nazwiska piłkarza z nazwy pliku
            parts = file_name.split("_")
            if len(parts) < 2:
                continue  # Pomijamy pliki o niewłaściwym formacie

            player_name = parts[1]  # Drugi element to nazwisko

            # Wczytanie danych z Excela
            try:
                df = pd.read_excel(file_path)
            except Exception as e:
                print(f"Błąd wczytywania pliku {file_name}: {e}")
                continue

            # Dodanie do słownika
            if player_name not in players_data:
                players_data[player_name] = []

            players_data[player_name].append(df)

# Tworzenie i zapisywanie plików zbiorczych dla każdego piłkarza
output_path = "Raw files GPS\Raw files GPS Zagłębie"  # <-- Zmień na właściwą ścieżkę
os.makedirs(output_path, exist_ok=True)

for player, dfs in players_data.items():
    combined_df = pd.concat(dfs, ignore_index=True)
    output_file = os.path.join(output_path, f"wyniki_calosciowe_{player}.xlsx")
    combined_df.to_excel(output_file, index=False)
    print(f"Zapisano: {output_file}")

print("Zakończono łączenie danych.")
