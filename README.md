# MarkItSwift

<img src="app.png" width="96" align="right" alt="MarkItSwift icon" />

แอปเดสก์ท็อป (CustomTkinter) สำหรับแปลงไฟล์เอกสารเป็น Markdown อย่างรวดเร็ว — รองรับ PDF, Word, Excel, PowerPoint, HTML, CSV, รูปภาพ ฯลฯ พร้อมลาก-วางไฟล์และแพ็กเป็น `.exe` ได้

ขับเคลื่อนด้วย [markitdown](https://github.com/microsoft/markitdown) ของ Microsoft

## ติดตั้ง

```bash
pip install -r requirements.txt
```

## รันแอป

```bash
python markitdown_ui.py
```

## วิธีใช้

1. กด **เลือกไฟล์...** แล้วเลือกเอกสาร — หรือ **ลากไฟล์มาวาง** ในโซนลาก-วาง (แปลงให้อัตโนมัติ)
2. กด **แปลงเป็น Markdown**
3. **คัดลอก** หรือ **บันทึก .md** ผลลัพธ์

> ลาก-วางไฟล์ใช้ `tkinterdnd2` ถ้าไม่ได้ติดตั้ง แอปยังทำงานได้ปกติ (ใช้ปุ่มเลือกไฟล์แทน)

## แพ็กเป็น .exe

ดับเบิลคลิก `build_exe.bat` (หรือรันในคอมมานด์พรอมต์) — จะได้ไฟล์ที่ `dist\MarkItSwift.exe`

โดยเบื้องหลังใช้คำสั่ง:

```bash
pyinstaller --onefile --windowed --name MarkItSwift ^
  --icon app.ico --add-data "app.ico;." ^
  --collect-all customtkinter --collect-all markitdown --collect-all tkinterdnd2 ^
  markitdown_ui.py
```

> หมายเหตุ: ไฟล์เสียง (mp3/wav) ต้องมี `ffmpeg` ในเครื่องจึงจะถอดเสียงได้; ฟีเจอร์อื่นไม่ต้องใช้

## Build อัตโนมัติ (GitHub Actions)

ทุกครั้งที่ push ขึ้น `main` ระบบจะ build `.exe` บน Windows ให้อัตโนมัติ — ดาวน์โหลดได้จากแท็บ **Actions › (run ล่าสุด) › Artifacts**

**ออก Release พร้อมไฟล์ .exe** — สร้าง tag ที่ขึ้นต้นด้วย `v`:

```bash
git tag v1.0.0
git push origin v1.0.0
```

Workflow จะ build แล้วแนบ `MarkItSwift.exe` เข้ากับ GitHub Release ให้เอง

## สร้างไอคอนใหม่ (ถ้าต้องการ)

```bash
python make_icon.py   # สร้าง app.ico และ app.png
```

## Credits

- การแปลงเอกสารทั้งหมดทำโดย [**markitdown**](https://github.com/microsoft/markitdown) (Microsoft, MIT License)
- UI ใช้ [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) และ [tkinterdnd2](https://github.com/pmgagne/tkinterdnd2)

## License

MIT — ดู [LICENSE](LICENSE) © 2026 Sitthisak C. "ball"
