# Kospel C.MI Register Mapping — UI Analysis

> **Language:** This document is in Polish. It was generated from analysis of the manufacturer's web UI JavaScript. It provides a reference mapping of registers to UI variables and meanings. For the library's register implementation, see [registers/README.md](../src/kospel_cmi/registers/README.md).

---

# Mapowanie rejestrów Kospel C.MI – analiza interfejsu UI

Dokument wygenerowany na podstawie analizy kodu JavaScript interfejsu webowego Kospel (http://192.168.101.49/65).
Źródło: pobrany HTML z inline script, wyciągnięte wywołania `getReg`, `setReg`, `setRegBit`, `getRegBit` oraz mapowania `data["0bXX"]`.

## Blok główny (getReg("0b2f", "30"))

Interfejs odświeża ekran startowy odczytem 30 rejestrów od 0b2f. Poniżej mapowanie na zmienne JS:

| Rejestr | Zmienna UI | Znaczenie | Format |
|---------|------------|-----------|--------|
| 0b2f | temp_zas_nas | Temperatura zasilania nastawa (setpoint) | ×10 °C |
| 0b30 | — | Tryb zasobnika CWU: 0=ekonomiczny, 1=przeciwzamrożeniowa, 2=komfort | int |
| 0b31 | temp_prog | Temperatura nastawy pokojowej | ×10 °C |
| 0b32 | — | Tryb pokojowy: 0=ekonomiczny, 1=przeciwzamrożeniowa, 2=komfort, 3=komfort-, 4=komfort+, 64=ręczny | int |
| 0b34 | pwr | Moc kotła | ×10 |
| 0b44 | temp_factor | Współczynnik temperatury | ×10 |
| 0b46 | moc | Moc załączona | ×10 |
| 0b48 | temp_in | Temperatura wlotowa (inlet) | ×10 °C |
| 0b49 | temp_out | Temperatura wylotowa (outlet) | ×10 °C |
| 0b4a | temp_zas | Temperatura zasobnika CWU | ×10 °C |
| 0b4b | temp_room | Temperatura pokojowa | ×10 °C |
| 0b4c | temp_out | Temperatura zewnętrzna | ×10 °C |
| 0b4e | preasure | Ciśnienie | ×100 bar |
| 0b4f | flow | Przepływ | ×10 l/min |
| 0b50 | r_flagi_2 | Flagi odczytu 2 | bity |
| 0b51 | r_flagi_1 | Flagi odczytu 1 / status komponentów | bity |
| 0b52 | error | Kod błędu | int |
| 0b54 | rw_flagi_2 | Flagi konfiguracji (R/W) | bity |
| 0b55 | rw_flagi_1 | Flagi systemowe (R/W) | bity |

## Rejestr 0b51 – status komponentów (bity)

| Bit | Znaczenie |
|-----|-----------|
| 0 | Pompa obiegowa CO (wl/wyl) |
| 1 | Pompa cyrkulacyjna CWU |
| 2 | Zawór trójdrogowy |
| 3 | Wejście NA |
| 4 | Wejście RP |
| 6 | Wejście FUN |
| 7 | Obwód CO aktywny (ikona radiatora) |
| 8 | Obwód CWU aktywny (ikona kranu) |

## Rejestr 0b55 – flagi systemowe (bity)

| Bit | Znaczenie |
|-----|-----------|
| 0 | Zasobnik CWU włączony |
| 1 | Czujnik zewnętrzny |
| 2 | (regulacja) |
| 3 | Tryb lato (summer) |
| 4 | Zasobnik CO włączony (co_yes_no) |
| 5 | Tryb zima (winter) |
| 6 | Tryb party |
| 7 | Tryb wakacje |
| 8 | Pompa – praca automatyczna |
| 9 | Tryb ręczny |
| 11 | Turbo automatycznie |
| 12 | Nastawa CO ręczna/auto |
| 13 | Ładowanie poza programem |
| 14 | (re) |
| 15 | (kn) |

## Rejestr 0b54 – flagi konfiguracji (bity)

| Bit | Znaczenie |
|-----|-----------|
| 2 | Cyrkulacja CWU włączona |
| 3 | Automatyczna zmiana czasu |
| 5 | Dezynfekcja z cyrkulacją |
| 6 | Dezynfekcja natychmiastowa |
| 7 | Dezynfekcja automatyczna |
| 8 | Kontrola ciśnienia |
| 13 | Odpowietrzanie pompy |

## Rejestry trybu party / wakacje

| Rejestr | Znaczenie |
|---------|-----------|
| 0b6c | Czas zakończenia – minuta (0–59) |
| 0b6d | Czas zakończenia – godzina (0–23) |
| 0b6e | Czas zakończenia – dzień (1–31) |
| 0b6f | Czas zakończenia – miesiąc (1–12) |
| 0b70 | Czas zakończenia – rok (2 cyfry, +2000) |

## Rejestry trybu ręcznego

| Rejestr | Znaczenie |
|---------|-----------|
| 0b8d | Temperatura ręczna | ×10 °C |
| 0bcc | Temperatura ręczna min (zakres) | ×10 °C |
| 0bcd | Temperatura ręczna max (zakres) | ×10 °C |

**Uwaga:** Aby 0b8d (temperatura ręczna) była używana przez firmware, rejestr 0b32 (tryb pokojowy) musi być ustawiony na 64 (ręczny). Dla CWU: 0b30 wybiera 0b66 (ekonomia) vs 0b67 (komfort).

## Temperatury pokojowe

| Rejestr | Znaczenie |
|---------|-----------|
| 0b63 | Temperatura party + wakacje (zakodowane) |
| 0b64 | Temperatura wakacje (indeks) |
| 0b68 | Temperatura ekonomiczna | ×10 °C |
| 0b69 | Temperatura komfort minus | ×10 °C |
| 0b6a | Temperatura komfortowa | ×10 °C |
| 0b6b | Temperatura komfort plus | ×10 °C |

## Temperatury CWU (zasobnik)

| Rejestr | Znaczenie |
|---------|-----------|
| 0b66 | Temperatura ekonomiczna | ×10 °C |
| 0b67 | Temperatura komfortowa | ×10 °C |
| 0bbe | Temperatura min (zakres) | ×10 °C |
| 0bbf | Temperatura max (zakres) | ×10 °C |

## Temperatury bufora CO

| Rejestr | Znaczenie |
|---------|-----------|
| 0b8c | Temperatura zasilania | ×10 °C |
| 0b8e | Temperatura zasilania (konfiguracja) | ×10 °C |
| 0bda | Temperatura dezynfekcji min | ×10 °C |
| 0bdb | Temperatura dezynfekcji max | ×10 °C |
| 0bdc | Czas dezynfekcji min | min |
| 0bdd | Czas dezynfekcji max | min |

## Dezynfekcja

| Rejestr | Znaczenie |
|---------|-----------|
| 0b76 | Temperatura dezynfekcji | ×10 °C |
| 0b77 | Dzień tygodnia dezynfekcji |
| 0b78 | Godzina dezynfekcji |
| 0b79 | Czas trwania dezynfekcji | min |

## Konfiguracja obiegu CO

| Rejestr | Znaczenie |
|---------|-----------|
| 0b71 | Numer krzywej grzania (cv) |
| 0b72 | Przesunięcie krzywej (cp) | ×10 lub int |
| 0b73 | Temperatura zasilania ręczna (tman) | ×10 °C |
| 0b74 | Temperatura zewnętrznego wyłączenia (toff) | ×10 °C |
| 0b7b | Temperatura zasilania max (tmax) | ×10 °C |
| 0bca | Przesunięcie krzywej min | ×10 lub int |
| 0bcb | Przesunięcie krzywej max | ×10 lub int |
| 0bc2 | Temperatura wylotowa min | ×10 °C |
| 0bc3 | Temperatura wylotowa max | ×10 °C |
| 0bc8 | Numer krzywej grzania min |
| 0bc9 | Numer krzywej grzania max |

## Konfiguracja zasobnika CWU

| Rejestr | Znaczenie |
|---------|-----------|
| 0bbc | Temperatura min (zakres) | ×10 °C |
| 0bbd | Temperatura max (zakres) | ×10 °C |

## Temperatura pokojowa – regulacja

| Rejestr | Znaczenie |
|---------|-----------|
| 0b75 | Histereza | ×10 °C |
| 0bc6 | Histereza min (zakres) | ×10 °C |
| 0bc7 | Histereza max (zakres) | ×10 °C |

## Tryb turbo

| Rejestr | Znaczenie |
|---------|-----------|
| 0b81 | Histereza trybu turbo |
| 0be0 | Histereza turbo min (zakres) | ×10 °C |
| 0be1 | Histereza turbo max (zakres) | ×10 °C |

## Pompa

| Rejestr | Znaczenie |
|---------|-----------|
| 0b58 | Typ pompy (Wilo/Grundfos) |
| 0b59 | Godzina ochrony pompy |
| 0b82 | Regulacja pompy |
| 0b83 | Wysokość podnoszenia | m |

## Moc kotła i tryb pracy

| Rejestr | Znaczenie |
|---------|-----------|
| 0b25 | Ilość dostępnych opcji wysokości podnoszenia pompy | Kolejne rejestry (od `0b26`) zawierają wartości dla każdego indeksu (0, 1, 2...) |
| 0b34 | Aktualna moc kotła | ×10 kW |
| 0b35 | Ilość dostępnych opcji maksymalnej mocy kotła | Kolejne rejestry (od `0b36`) zawierają wartości (w ×10 kW) dla każdego indeksu (0, 1, 2...). Liczba opcji zależy od sprzętu. |
| 0b62 | Wybrany indeks maksymalnej mocy kotła | Zapisywany jako indeks (0, 1, 2...) wybranej z listy opcji zdefiniowanej w `0b35`. Nie wpisujemy tu wartości kW! |
| 0b7f | Tryb pracy: 0=podstawowy, 1=źródło ciepła, 2=bufor |
| 0b8a | Tryb pracy: 0=CO, 1=źródło ciepła, 2=bufor |
| 0be5 | Tryb pracy min (zakres) |
| 0be6 | Tryb pracy max (zakres) |

## Zegar RTC (0af6–0afc)

| Rejestr | Znaczenie |
|---------|-----------|
| 0af6 | Sekunda |
| 0af7 | Minuta |
| 0af8 | Godzina |
| 0afa | Dzień |
| 0afb | Miesiąc |
| 0afc | Rok (2 cyfry, +2000) |

## Programy tygodniowe

### Program CO (0c94–0c9a)

| Rejestr | Znaczenie |
|---------|-----------|
| 0c94 | Poniedziałek |
| 0c95 | Wtorek |
| 0c96 | Środa |
| 0c97 | Czwartek |
| 0c98 | Piątek |
| 0c99 | Sobota |
| 0c9a | Niedziela |

### Program CWU (0d16–0d1c)

| Rejestr | Znaczenie |
|---------|-----------|
| 0d16 | Poniedziałek |
| 0d17 | Wtorek |
| … | … |
| 0d1c | Niedziela |

### Program cyrkulacji (0d98–0d9e)

| Rejestr | Znaczenie |
|---------|-----------|
| 0d98 | Poniedziałek |
| … | … |
| 0d9e | Niedziela |

## Inne

| Rejestr | Znaczenie |
|---------|-----------|
| 0b53 | Restart kotła (bit 0) |

## Rejestry NIE używane w UI

Na podstawie live scannera zmieniają się, ale nie występują w kodzie UI:

- **0b2d** – flaga/stan (0000/ffff/0100)
- **0b3f** – ~15.6 °C (prawdopodobnie temperatura)
- **0b40** – ~1262 (prawdopodobnie licznik energii/czasu)

Te rejestry są aktualizowane wyłącznie przez firmware.
