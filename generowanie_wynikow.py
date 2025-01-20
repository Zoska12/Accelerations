import pandas as pd
import re

file_path = "15.01 Tr. 6 Export for Patryk Kusztal 45648.csv"

# Pobranie imienia i nazwiska z sekcji # Athlete
with open(file_path, 'r', encoding='utf-8') as file:
    lines = file.readlines()


athlete_line = next((line for line in lines if "# Athlete" in line), None)
if athlete_line:
    match = re.search(r'"(\w+)"', athlete_line)
    if match:
        athlete_name = match.group(1)
        output_file = f'wyniki_{athlete_name}.xlsx'
    else:
        output_file = 'wyniki.xlsx'
else:
    output_file = 'wyniki.xlsx'

# Znalezienie wiersza nagłówka (pierwszy wiersz zawierający "Velocity" jako kolumnę)
header_line = next(i for i, line in enumerate(lines) if "Velocity" in line)

# Wczytanie pliku od linii nagłówka
df = pd.read_csv(file_path, skiprows=header_line, sep=';', decimal=',')

# Obliczenie średniej ruchomej (każda obserwacja + 4 kolejne wartości)
#df['Velocity_SMA'] = df['Velocity'].rolling(window=5, min_periods=1).mean()
def compute_future_mean(series, window=7):
    return [series[i:i+window].mean() if i+window <= len(series) else None for i in range(len(series))]

df['Acceleration_SMA'] = compute_future_mean(df['Acceleration'], window=7)

# Definiowanie dynamicznych przedziałów co 5 jednostek
max_velocity = df['Velocity'].max()  # Pobranie maksymalnej wartości
bins = list(range(0, int(max_velocity) + 6, 5))  # Tworzenie przedziałów co 5
labels = [f"{bins[i]}-{bins[i+1]}" for i in range(len(bins)-1)]  # Generowanie etykiet

# Przypisanie wartości do przedziałów
df['Velocity_Bin'] = pd.cut(df['Velocity'], bins=bins, labels=labels, right=False)

# Znalezienie wszystkich wartości przyspieszenia dla każdej grupy z warunkiem minimalnej odległości 1s
def filter_by_time_gap(group):
    selected = []
    top_n = 10  # Początkowa liczba wybranych wartości
    while len(selected) < 10:
        candidates = group.nlargest(top_n, 'Acceleration_SMA')  # Pobieramy dynamicznie rosnącą liczbę wyników
        selected = []
        for _, row in candidates.iterrows():
            if not selected or all(abs(row['Seconds'] - prev['Seconds']) >= 1 for prev in selected):
                selected.append(row)
            if len(selected) == 10:
                break
        top_n += 5  # Zwiększamy liczbę wybieranych kandydatów, jeśli nie osiągnęliśmy 10 obserwacji
        if top_n > len(group):  # Jeśli już nie mamy więcej danych, przerywamy pętlę
            break
    return pd.DataFrame(selected)

top_acceleration_by_bin = (
    df.groupby('Velocity_Bin', group_keys=False)
    .apply(filter_by_time_gap)
    .sort_values(by=['Velocity_Bin', 'Seconds'])
    .reset_index(drop=True)[['Timestamp', 'Seconds', 'Velocity', 'Acceleration_SMA', 'Velocity_Bin']]
)
# Zapis wyników do pliku
top_acceleration_by_bin.to_excel(output_file, index=False)

print(f'Wyniki zapisane w pliku {output_file}')