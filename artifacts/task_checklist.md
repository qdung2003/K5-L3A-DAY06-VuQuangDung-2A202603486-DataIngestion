# Checklist thuc te

Da hoan thanh trong workspace: corpus/manifest/quyen (7–13), benchmark frozen 20 cau 15/5, evidence/filter validation (15–22), ingestion/chunking/embedding/store/evaluation/run (23–31), A/B/C ingest/reload/top-3/trace/metrics (32–38), retrieval metrics va audit artifacts (39–45), experiment log/results/report/README/STUDENT (46–54, 56–57), hybrid tuy chon (58).

Cac muc can dieu kien ben ngoai hoac xac nhan cua hoc vien:
- Giai doan 0.1–0.4: Python da co; Docker khong co tren may nen PostgreSQL setup chua chay. Backend thi nghiem duoc thay bang Chroma PersistentClient theo GUIDE; check_setup.py Chroma dat Setup OK.
- 0.5–0.6: model that da tai, hash va cache; khong can API key.
- 55: repo ca nhan da duoc cung cap: https://github.com/qdung2003/K5-L3A-DAY06-VuQuangDung-2A202603486-DataIngestion. Kenh nop cho giang vien va deadline chua duoc cung cap; khong tu nhan da nop qua kenh lop.
- 44/49: nhan hien tai do Codex doc/cham, phieu author_review_pending.csv con trong; bao cao khong nhan la human audit.
- 51: STUDENT.md da ghi repo, commit ma nguon/ket qua va cach xac dinh HEAD cua ban nop hien tai.
- 52–53: gioi han va rubric da doi chieu trong bao cao; khong tu tuyen bo diem.
- Corpus la text RST, khong PDF: physical page = N/A; page ID la don vi truy vet theo GUIDE, khong gia mao so trang.
- Chua dung hybrid de chinh baseline/test; hybrid co holdout rieng va ket qua phu trong results/hybrid.

Khong commit starter/.env, model weights, Chroma DB, rerun output hoac secrets. Chay starter/scripts/verify_submission.py truoc khi dong goi.
