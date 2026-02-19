# Air Quality Analysis Dashboard: Aotizhongxin Station

## Deskripsi Proyek
Proyek ini bertujuan untuk menganalisis data kualitas udara dari stasiun Aotizhongxin (Beijing) periode 2013-2017. Analisis difokuskan pada tren tingkat polusi PM2.5 dan hubungannya dengan faktor cuaca. Hasil analisis disajikan dalam bentuk dashboard interaktif menggunakan Streamlit.

## Struktur File
```
.
├── dashboard/
│   ├── dashboard.py       # Script utama untuk menjalankan dashboard
│   └── main_data.csv      # Data hasil cleaning yang digunakan oleh dashboard
├── data/
│   └── PRSA_Data_Aotizhongxin_20130301-20170228.csv  # Dataset mentah
├── notebook.ipynb         # Notebook Jupyter berisi analisis data lengkap
├── analysis_script.py     # Script Python alternatif untuk analisis dan cleaning data
├── requirements.txt       # Daftar pustaka yang dibutuhkan
└── README.md              # Dokumentasi proyek
```

## Cara Menjalankan Proyek

### 1. Setup Environment
Pastikan Anda memiliki Python terinstal. Disarankan menggunakan virtual environment.

```bash
# Buat virtual environment (opsional)
python -m venv venv
source venv/bin/activate  # Untuk Mac/Linux
# venv\Scripts\activate   # Untuk Windows
```

### 2. Install Dependencies
Install library yang diperlukan:

```bash
pip install -r requirements.txt
```

### 3. Menjalankan Analisis Data (Opsional)
Jika ingin melihat proses analisis atau membuat ulang data bersih:
- Buka `notebook.ipynb` menggunakan Jupyter Notebook, atau
- Jalankan script analisis:
  ```bash
  python analysis_script.py
  ```

### 4. Menjalankan Dashboard
Jalankan perintah berikut untuk membuka dashboard Streamlit:

```bash
streamlit run dashboard/dashboard.py
```

Dashboard akan terbuka di browser default Anda (biasanya di `http://localhost:8501`).

## Penjelasan Singkat
- **Notebook**: Melakukan loading data, cleaning (handling missing values), EDA, dan visualisasi untuk menjawab pertanyaan bisnis.
- **Dashboard**: Menampilkan metrik utama, tren waktu PM2.5, dan distribusi kategori kualitas udara secara interaktif dengan filter tanggal.
