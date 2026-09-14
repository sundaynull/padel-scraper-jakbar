# DKI Jakarta Padel Court Data Pipeline and Market Intelligence

Automated data pipeline untuk ekstraksi data operasional, estimasi okupansi, dan proyeksi potensi omzet venue olahraga padel di 5 wilayah Kota Administrasi DKI Jakarta secara terjadwal.

Repositori ini berfungsi sebagai modul pengumpulan data eksternal independen (data ingestion pipeline) guna mendukung pengawasan kepatuhan Pajak Barang dan Jasa Tertentu (PBJT) pada sektor jasa kesenian, hiburan, dan kebugaran (Bappenda Provinsi DKI Jakarta).

---

## 1. Fitur Utama

- Cakupan 5 Wilayah DKI Jakarta: Menjangkau Jakarta Barat, Jakarta Selatan, Jakarta Pusat, Jakarta Utara, dan Jakarta Timur.
- Validasi Venue Aktif: Menyaring dan mengabaikan venue berstatus coming soon atau tanpa jadwal lapangan operasional secara otomatis.
- Penanganan Pembatalan (Cancellation Handling): Menerapkan mekanisme deduplikasi berbasis slot_key (drop_duplicates keep='last') untuk mengoreksi status pembatalan sewa secara historis.
- Multi-Sheet Export: Mengagregasi hasil ekstraksi seluruh kota administrasi ke dalam 1 berkas kerja Excel (.xlsx) multi-sheet terstruktur.
- Otomatisasi Penuh (CI/CD): Terintegrasi dengan GitHub Actions yang berjalan otomatis 4 kali sehari (05:30, 11:30, 17:30, dan 21:30 WIB).

---

## 2. Arsitektur Alur Kerja

```text
[ayo.co.id Platform]
         │
         ▼
[extract_all_venues] ────► Filter Wilayah & Cabor Padel
         │
         ▼
[get_venue_details]  ────► Validasi ID & Status Operasional
         │
         ▼
 [get_field_ids]     ────► Identifikasi Unit Court Aktif
         │
         ▼
  [scrape_slots]     ────► Ekstraksi Slot, Tarif, & Status
         │
         ▼
[Data Reconciliation] ──► Deduplikasi Overwrite (Slot Cancellation)
         │
         ▼
[Multi-Sheet Excel]  ────► Auto-Commit ke Repositori via GitHub Actions
