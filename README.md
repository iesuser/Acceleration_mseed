# Acceleration_mseed

სეისმური ტალღების (MiniSEED/FDSN) დამუშავების პროექტი, რომლის მიზანია მიწისძვრის ივენტებზე:

- აჩქარების არხებიდან (`HN*`) მაქსიმალური `g` მნიშვნელობების გამოთვლა;
- ზღურბლს გადაცილებული სადგურების არხების ექსპორტი ASCII-ში;
- ივენტის/სადგურის მიხედვით მოკლე შედეგების (`g_accelerations.txt`, `g_accelerations.csv`) გენერაცია;
- დამხმარე ექსპორტები (`MSEED`, `SAC`) და CSV merge workflow.

---

## რას აკეთებს პროექტი

პროექტში რეალურად ორი ძირითადი workflow-ია:

1. **Shakemap/event XML-ზე დაფუძნებული flow** (`app.py`)
   - იღებს სადგურებს `shakemaps/<event_id>/input/event_dat.xml`-დან;
   - ადარებს picks-ს `scxmldump` შედეგთან (`dump/*.xml`);
   - საჭიროების შემთხვევაში ითვლის P-wave მისვლის დროს მანძილის მიხედვით;
   - ბოლოს იძახებს `print_acc.py`-ს და ინახავს ASCII ტრეისებს.

2. **FDSN waveforms-ზე დაფუძნებული flow** (`acceleration.py`)
   - იღებს `HN*` არხებს მითითებული origin time-ის გარშემო;
   - აშორებს ინსტრუმენტულ response-ს (`output="ACC"`);
   - ითვლის მაქსიმალურ `g` აჩქარებას;
   - თუ სადგური გადაცდა `G_THRESHOLD`-ს, ინახავს არხებს ASCII ფორმატში;
   - ქმნის შემაჯამებელ ფაილებს (`g_accelerations.txt`, `g_accelerations.csv`);
   - პარალელურად ითხოვს `HH*` (velocity) არხებს შერჩეული სადგურებისთვის და ასევე ინახავს მათ ASCII-ს.

---

## პროექტის სტრუქტურა

ძირითადი სკრიპტები:

- `acceleration.py` - მთავარი დამუშავების სკრიპტი threshold-ზე დაფუძნებული ექსპორტისთვის.
- `calc_acceleration.py` - ბაჩური გაშვება CSV-დან (სტრიქონობრივად იძახებს `acceleration.py`-ს).
- `app.py` - shakemap + dump XML workflow და სადგურების არჩევა.
- `print_acc.py` - კონკრეტული სადგურების waveform/ascii ექსპორტი.
- `print_vel_acc.py` - ერთ სადგურზე ACC vs VEL->ACC შედარებითი ტესტი (კონსოლური).
- `plot_acceleration.py` - სწრაფი plot/debug სკრიპტი.
- `export_mseed.py` - waveform ექსპორტი MiniSEED სტრუქტურაში.
- `export_sac.py` - waveform ექსპორტი SAC ფორმატში.
- `merged_station.py` - `acc_stations.csv` + `station_coordinates.csv` merge -> `merged_output.csv`.
- `change_channels.py` - ლოკალურ MSEED ფაილებში არხის სახელის კორექცია (`HHE` -> `HNE`).

ნოუთბუქები:

- `plot_vel_acc.ipynb`
- `plot_ascii.ipynb`
- `read_SAC.ipynb`

---

## მოთხოვნები და გარემო

- Python 3.10+ (რეკომენდებული: 3.12)
- Linux/macOS გარემო
- ქსელური წვდომა FDSN სერვერზე (სკრიპტებში hardcoded მისამართებია)
- `scxmldump` CLI საჭიროა `app.py` workflow-სთვის

დამოკიდებულებების დაყენება:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## სწრაფი გაშვება

### 1) ბაჩური დამუშავება CSV-დან (რეკომენდებული არსებული flow-თვის)

`test_eq.csv` ფორმატი:

```csv
id,origin_time,latitude,longitude,ml,stationCode,epicenterDistance
555188,2025-03-08 11:28:25.120,42.395,45.107,4.22,CHBG,256.9
```

გაშვება:

```bash
python3 calc_acceleration.py
```

`calc_acceleration.py` თითოეულ row-ზე იძახებს:

```bash
python3 acceleration.py <event_id> <latitude> <longitude> <origin_time>
```

### 2) ერთჯერადი გაშვება პირდაპირ

```bash
python3 acceleration.py 555188 42.395 45.107 "2025-03-08 11:28:25.120"
```

---

## Output სტრუქტურა

`acceleration.py` ქმნის დირექტორიებს:

```text
temp/<YEAR>/<ORIGIN_TIME>/
```

და შიგნით:

- `<STATION>/...ascii` - threshold-ს გადაცილებული სადგურების არხები (ACC და შესაბამისი VEL არხები);
- `g_accelerations.txt` - ტექსტური summary (`Station, Max g`);
- `g_accelerations.csv` - მინიმალური CSV ფორმატი:
  - `id, latitude, longitude, station`

ლოგები ინახება:

- `logs/print_acc.log`
- `logs/export_mseed.log`
- `logs/vel2_acc.log`
- `ies_acc_log` (legacy logger `print_and_log.py`-დან)

---

## კონფიგურაცია (სად რა იცვლება)

ყველაზე ხშირად შესაცვლელი ადგილები:

- `acceleration.py`
  - `FDSN_CLIENT` (სერვერის მისამართი)
  - `NETWORK`, `CHANNEL_ACC`, `CHANNEL_VEL`
  - `G_THRESHOLD`
  - `STANDALONE_STATIONS`
  - `STATION_DICT` (station code map)

- `app.py`
  - `ip_address` (`scxmldump` წყარო)
  - `shakemaps_path`
  - `acc_limit`

- `print_acc.py`
  - `LOCATION` (ამჟამად `'20'`)
  - FDSN endpoint

---

## მონაცემთა ფაილები

- `earthquakes.csv` - ივენტების სია ისტორიული დამუშავებისთვის.
- `test_eq.csv` - სწრაფი/სატესტო ერთ-ივენტიანი input.
- `acc_stations.csv` - ივენტი-სადგურის list (`id, latitude, longitude, station`).
- `station_coordinates.csv` - სადგურების კოორდინატები.
- `merged_output.csv` - merge-ის შედეგი (`merged_station.py`).

---

## შენიშვნები

- ბევრი პარამეტრი hardcoded-ია (endpoint-ები, channel masks, time windows), ამიტომ production გამოყენებისთვის რეკომენდებულია კონფიგურაცია `.env`/CLI არგუმენტებზე გადატანა.
- პროექტში არის კვლევითი/სატესტო სკრიპტებიც (`plot_*`, `print_vel_acc.py`, notebook-ები), რომლებიც ძირითად pipeline-ს არ წარმოადგენენ.
- `.gitignore` უკვე გამორიცხავს `venv/`, `temp/`, `logs/`.

---

## შესაძლო გაუმჯობესებები

- unified CLI (`argparse`) ყველა სკრიპტისთვის;
- ერთი საერთო config ფაილი endpoint-ებისა და ზღურბლებისთვის;
- ავტომატური ტესტები CSV parsing-ზე და output ფორმატზე;
- Dockerfile reproducible გარემოსთვის.
