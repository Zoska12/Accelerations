import pandas as pd
import re

file_path = "15.01 Tr. 6 Export for Patryk Kusztal 45648.csv"

# Definiowanie zakresu godzinowego
start_time = "18:15"
end_time = "18:30"

podzial = {'Mała Gra':[start_time,end_time],
           'Duża Gra':["18:30","18:45"]}

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

df['Timestamp'] = pd.to_datetime(df['Timestamp'], format="%d.%m.%Y %H:%M")

results=[]
for key, value in podzial.items():
    # Konwersja na obiekty czasu
    df_filtred = df[(df['Timestamp'].dt.time >= pd.to_datetime(value[0], format='%H:%M').time()) & 
                    (df['Timestamp'].dt.time <= pd.to_datetime(value[1], format='%H:%M').time())]

    # Definiowanie dynamicznych przedziałów co 5 jednostek
    max_velocity = df['Velocity'].max()  # Pobranie maksymalnej wartości
    bins = [5, 10, 15]  # Dwa przedziały: 5-10 i 10-15
    labels = ["5-10", "10-15"]

    # Przypisanie wartości do przedziałów
    df_filtred['Velocity_Bin'] = pd.cut(df_filtred['Velocity'], bins=bins, labels=labels, right=False)

    df_filtred['Trening']=key
    # Znalezienie wszystkich wartości przyspieszenia dla każdej grupy z warunkiem minimalnej odległości 1s
    def filter_by_time_gap(group):
        selected = []
        top_n = 3  # Początkowa liczba wybranych wartości
        while len(selected) < 3:
            candidates = group.nlargest(top_n, 'Acceleration_SMA')  # Pobieramy dynamicznie rosnącą liczbę wyników
            selected = []
            for _, row in candidates.iterrows():
                if not selected or all(abs(row['Seconds'] - prev['Seconds']) >= 1 for prev in selected):
                    selected.append(row)
                if len(selected) == 3:
                    break
            top_n += 3  # Zwiększamy liczbę wybieranych kandydatów, jeśli nie osiągnęliśmy 10 obserwacji
            if top_n > len(group):  # Jeśli już nie mamy więcej danych, przerywamy pętlę
                break
        return pd.DataFrame(selected)
    

    top_acceleration_by_bin = (
        df_filtred.groupby('Velocity_Bin', group_keys=False)
        .apply(filter_by_time_gap)
        .sort_values(by=['Velocity_Bin', 'Seconds'])
        .reset_index(drop=True)[['Timestamp', 'Seconds', 'Velocity', 'Acceleration_SMA', 'Velocity_Bin','Trening']]
    )
    results.append(top_acceleration_by_bin)
# Zapis wyników do pliku

final_results = pd.concat(results, ignore_index=True)

final_results.to_excel(output_file, index=False)

print(f'Wyniki zapisane w pliku {output_file}')