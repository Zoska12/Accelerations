import pandas as pd
import re
import os

def process_file(file_path):
    """
    Przetwarza plik CSV zawierający dane sportowe, oblicza przedziały prędkości,
    średnią ruchomą przyspieszenia i wybiera 10 wartości dla każdej grupy prędkości.

    Parametry:
        file_path (str): Ścieżka do pliku CSV.

    Zwraca:
        pd.DataFrame: Przetworzony DataFrame.
    """

    # Pobranie imienia zawodnika z sekcji # Athlete
    with open(file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()

    athlete_line = next((line for line in lines if "# Athlete" in line), None)
    if athlete_line:
        match = re.search(r'"(\w+)"', athlete_line)
        athlete_name = match.group(1) if match else "Unknown"
    else:
        athlete_name = "Unknown"

    # Znalezienie wiersza nagłówka
    header_line = next(i for i, line in enumerate(lines) if "Velocity" in line)

    # Wczytanie danych do DataFrame
    df = pd.read_csv(file_path, skiprows=header_line, sep=';', decimal=',')

    # Obliczenie średniej ruchomej przyspieszenia (7 przyszłych wartości)
    def compute_future_mean(series, window=7):
        return [series[i:i+window].mean() if i+window <= len(series) else None for i in range(len(series))]

    df['Acceleration_SMA'] = compute_future_mean(df['Acceleration'], window=7)

    # Definiowanie dynamicznych przedziałów prędkości co 5 jednostek
    max_velocity = df['Velocity'].max()
    bins = list(range(0, int(max_velocity) + 6, 5))  # Przedziały co 5
    labels = [f"{bins[i]}-{bins[i+1]}" for i in range(len(bins)-1)]

    df['Velocity_Bin'] = pd.cut(df['Velocity'], bins=bins, labels=labels, right=False)

    # Filtracja wartości przyspieszenia (10 największych wartości w każdej grupie prędkości)
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

    top_acceleration_by_bin = (
        df.groupby('Velocity_Bin', group_keys=False)
        .apply(filter_by_time_gap)
        .sort_values(by=['Velocity_Bin', 'Seconds'])
        .reset_index(drop=True)[['Timestamp', 'Seconds', 'Velocity', 'Acceleration_SMA', 'Velocity_Bin']]
    )

    # Zapis do pliku XLSX
    output_file = f'wyniki_{athlete_name}.xlsx'
    top_acceleration_by_bin.to_excel(output_file, index=False)

    print(f"Zapisano plik: {output_file}")
    return top_acceleration_by_bin
