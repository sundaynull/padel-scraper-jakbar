# Padel Scraper Jakbar

Automated web scraping pipeline berbasis Python dan GitHub Actions untuk mengekstraksi data ketersediaan slot reservasi lapangan padel di wilayah Kota Administrasi Jakarta Barat melalui platform agregator [ayo.co.id](https://ayo.co.id)[cite: 1]. 

Pipeline ini dirancang untuk memantau pergerakan okupansi harian dan menghitung akumulasi estimasi *gross revenue* secara granular berbasis harga riil per slot waktu (membedakan jam pagi, siang, dan jam sibuk/*prime time* malam).

---

## Cakupan & Fitur Scraping

* **Direktori Jakbar & Filtering Aktif:** Mengambil data seluruh venue padel terdaftar di Jakarta Barat dan secara otomatis memfilter venue berstatus persiapan (*coming soon* atau 0 unit lapangan) agar tidak merusak kalkulasi okupansi.
* **Ekstraksi Granular per Slot:** Menembak endpoint API internal direktori per venue dan per lapangan untuk mengambil parameter:
  * Jam mulai & jam selesai (`time_slot`)
  * Tarif sewa per jam riil (`price`)
  * Status ketersediaan (`Available` vs `Booked`)
* **Kalkulasi Estimasi Revenue:** Mengagregasi total potensi omzet dari seluruh slot berstatus `Booked` dikalikan harga riil masing-masing jam yang dipesan.
* **Penjadwalan Otomatis (CI/CD):** Dijalankan via GitHub Actions Cron 4x sehari tanpa memerlukan server fisik lokal.
* **Ekspor Data:** Menghasilkan snapshot data harian dalam format CSV bersih yang siap dikonsumsi oleh data warehouse, dashboard visualisasi, atau antarmuka aplikasi eksternal.

---
