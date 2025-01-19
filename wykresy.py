import matplotlib.pyplot as plt
import pandas as pd
import re

file_path = "15.01 Tr. 6 Export for Patryk Kusztal 45648.csv"

# Wyciągnięcie imienia i nazwiska z nazwy pliku
match = re.search(r"for (\w+) (\w+)", file_path)
if match:
    first_name, last_name = match.groups()
    output_file = f'wyniki_{first_name}_{last_name}.xlsx'
else:
    output_file = 'wyniki.xlsx'

# Ponownie wczytam plik, analizując jego zawartość, aby znaleźć odpowiedni wiersz nagłówków
with open(file_path, 'r', encoding='utf-8') as file:
    lines = file.readlines()

# Znalezienie wiersza nagłówka (pierwszy wiersz zawierający "Velocity" jako kolumnę)
header_line = next(i for i, line in enumerate(lines) if "Velocity" in line)

# Wczytanie pliku od linii nagłówka
df = pd.read_csv(file_path, skiprows=header_line, sep=';', decimal=',')

# Tworzenie wykresu
plt.figure(figsize=(12, 6))  # Zwiększenie rozmiaru wykresu


# Dodanie średniej kroczącej dla wygładzenia wykresu (rolling window = 20) - żeby było lepiej widać
df['Acceleration_Smooth'] = df['Acceleration'].rolling(window=20, min_periods=1).mean()
plt.plot(df['Seconds'][::5], df['Acceleration_Smooth'][::5], label='Smoothed Acceleration', color='red', linewidth=1.5)

# Opisy osi i tytuł
plt.xlabel('Czas (s)')
plt.ylabel('Acceleration Smooth')
plt.title('Acceleration')

# Dodanie siatki dla lepszej czytelności
plt.grid(True, linestyle='--', linewidth=0.5)

# Dodanie legendy
plt.legend()

# Wyświetlenie wykresu
plt.show()

# Tworzenie wykresu
plt.figure(figsize=(12, 6))  # Zwiększenie rozmiaru wykresu


df=df[df['Velocity']>5]
# Dodanie średniej kroczącej dla wygładzenia wykresu (rolling window = 20) - żeby było lepiej widać
df['Acceleration_Smooth'] = df['Acceleration'].rolling(window=20, min_periods=1).mean()
plt.plot(df['Seconds'], df['Acceleration'], label='Smoothed Acceleration', color='red', linewidth=1.5)

# Opisy osi i tytuł
plt.xlabel('Czas (s)')
plt.ylabel('Acceleration Smooth (Velocity>5)')
plt.title('Acceleration (Velocity>5)')

# Dodanie siatki dla lepszej czytelności
plt.grid(True, linestyle='--', linewidth=0.5)

# Dodanie legendy
plt.legend()

# Wyświetlenie wykresu
plt.show()