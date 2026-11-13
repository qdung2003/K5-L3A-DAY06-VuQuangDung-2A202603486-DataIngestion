# Phuong phap audit va gioi han nguoi cham

Nguoi doc/cham hien tai: **Codex (AI assistant)**. Tac gia bai: Vu Quang Dung. **Chua co xac nhan tac gia da tu cham hoac nguoi doc lap kiem tra.** Khong gan nhan nay thanh human/manual audit.

Mau da chot truoc retrieval trong benchmark/freeze.json. Coherence: 10 page ID dau theo thu tu tu dien classes:001–010, vi tri len(text)//2; chunk co start nho nhat chua vi tri. Doc chunk cung full source_text trong coherence_samples.json, cham 0–2 theo GUIDE. B/C giu nguyen chunk, vi vay nhan bang nhau la chu dich.

Grounding: doc du text top-3 cua Q16–Q20 cho tung A/B/C, doi chieu question/expected answer va nguon; cham 0 khong evidence, 1 co lien quan nhung thieu dieu kien, 2 du tra loi/truy nguon. Nhan duoc quyet dinh theo noi dung, khong lay tu hit_at_3. Vi du A/Q18 co source page dung nhung chi co double-underscore name mangling; khong du tra loi quy uoc single underscore → 0. B/Q16 rank 1 chua du nhung rank 2 du → 2.

Metadata: doc bang 45 ban ghi test × top-3, so source URL, document_id, page ID, section voi manifest va normalized text. verify_store.py kiem tra rieng toan bo text/metadata da luu trung export. 15/15 moi strategy du+ dung; khong phat hien loi metadata.

Filter: native metadata values duoc doi chieu truc tiep tung hit. A/B khong bat filter nhung van do pham vi: A test 1/2, B test 2/2, C test 2/2. A/Q20 rank 3 thuoc stdlib thay vi stdlib2. B dat 2/2 tinh co tren tap nho; chi C bao dam ap dieu kien o backend.

Coherence A 1,1/2, B/C 1,7/2. Grounding A 1/0/4, mean 1,6/2; B/C 0/0/5, mean 2/2. Ly do va ID chunk o CSV labels. audit_summary.json gan hash trace.

Nguy co thien lech: cung AI soan benchmark, code, xem metric roi doc audit; khong blind, khong doc lap va chua co inter-rater agreement. Phieu author_review_pending.csv giu trong, tac gia can dien diem/ly do/ten/ngay that. Khi trace/input thay doi phai lay mau va doc/cham moi.
