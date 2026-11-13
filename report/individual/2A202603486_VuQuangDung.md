# Báo cáo cá nhân — Day 06

**Vũ Quang Dũng — 2A202603486 — L3A**

## Dữ liệu và pipeline

Chủ đề: cách dùng Python theo Python Tutorial CPython **v3.13.0**, tám chương tài liệu kỹ thuật tiếng Anh: controlflow, datastructures, modules, inputoutput, errors, classes, stdlib và stdlib2. [Manifest](../../data/manifest.json) ghi nguồn từng chương, thời điểm truy cập thực, snapshot, SHA-256, đường dẫn, đơn vị nguồn và số ký tự. [Raw và normalized](../../data/python_tutorial) được kèm để người chấm kiểm tra.

Corpus có **186.787 ký tự**, **93 đơn vị**: lần lượt **19/12/11/10/11/18/5/7** đơn vị theo tám chương trên. Không phải PDF, không có số trang vật lý. Quy tắc theo GUIDE: chia liên tục theo thứ tự, tại ranh giới đoạn sau ≥1.800 ký tự; nhập đuôi <1.500 vào đơn vị trước. Mỗi đơn vị ≥1.500 ký tự NFC, nhỏ nhất 1.522; không nhân bản hoặc overlap ở bước đếm corpus. Offset [start,end) trỏ vào chapter .txt. page là ID ví dụ classes:014. Không có scan/OCR, không dùng bìa/mục lục/trang references để đủ số lượng.

Quyền: PSF License Version 2 cho documentation; code examples/recipes còn dual-license 0BSD từ 3.8.6. Giữ [license gốc](../../data/python_tutorial/LICENSE.txt), [điều khoản documentation](../../data/python_tutorial/documentation-license.rst), copyright PSF và mô tả thay đổi trong [data/README](../../data/README.md). Nguồn công khai có giấy phép, không chứa dữ liệu mật/cá nhân của người dùng.

Pipeline: load/clean RST → đơn vị nguồn → chunk → model neural thật → Chroma persistent → top-3 → metric/trace/audit. normalize_text giữ NFC, newline, dòng trống và code indentation; xóa target/index/directive markup, giữ method signatures. load_pdf cũng hiện thực giữ physical page và ghi log trang không extract được; corpus lần này không dùng PDF. RST cleanup bằng regex chưa phải Sphinx renderer đầy đủ: có cross-reference/comment còn lại, có thể mất ngữ cảnh ở ranh giới đơn vị. Không tự OCR hoặc thay dữ liệu khi lỗi.

Model: **sentence-transformers/all-MiniLM-L6-v2**, commit **1110a243fdf4706b3f48f1d95db1a4f5529b4d41**, **384 chiều**, provider local CPU. Sentence Transformers **6.3.0**, PyTorch **2.15.0**, Transformers **5.22.2**, NumPy **2.5.4**. Query/document cùng tokenizer, mean pooling, L2 normalization, không prefix, query chỉ là question; max_seq_length **256 token**. [Model manifest](../../data/model_manifest.json) lưu hash từng file tải; không vector mock/fallback.

Store: **Chroma 1.5.9 PersistentClient**, path starter/vector_store, collection day06_a, day06_b, day06_c, cosine **approximate HNSW**, search_ef=100. Filter dùng native where, không ghép SQL. HNSW không có bảo đảm recall exact; filter hẹp có thể giảm số ứng viên/recall nên cần kiểm tra trace/số hit. Lần này mọi lượt có đủ 3 hit. Không đổi backend/model/metric giữa các cấu hình.

Metadata mỗi chunk: document_id:string, source:string URL, page:string unit ID. section:string lấy từ tên chapter upstream để phân biệt tám phạm vi; version:string lấy từ tag v3.13.0; language:string=en từ nội dung nguồn. start_char/end_char:int là offset trong đơn vị, unit_start/unit_end:int là offset trong chapter. section hữu ích vì người hỏi chỉ định chương từ trước; page giúp mở đúng ranh giới nguồn. Hạn chế: section quá thô, hai nội dung tương tự vẫn cùng phạm vi; version tag snapshot không phải ngày hiệu lực chính sách.

Upsert kiểm tra số vector, số chiều, hữu hạn, zero vector và duplicate ID. ID SHA-256 từ doc/page/method/span/text. Upsert full snapshot rồi xóa IDs ngoài snapshot, xử lý cả tài liệu đổi/xóa; không phải transaction atomic toàn bộ collection. Không chạy nhiều writer đồng thời; retry cùng snapshot sau lỗi. [Kiểm chứng bằng process mới](../../results/storage_verification.json) xác nhận lưu bền vững, toàn bộ text/metadata đúng export, nạp lại không trùng và snapshot 2→1 xóa ID cũ.

Lệnh setup/run: [README](../../README.md). Python **3.13.15**, Windows 11, CPU 4 threads. Đã chọn Chroma nên không cần Docker; máy chưa có Docker, không tuyên bố chạy được PostgreSQL. Không dùng API trả phí, **0 USD API**; chưa quy đổi điện/phần cứng/mạng. [run.json](../../results/run.json) ghi thời điểm **13/11/2026, 18:06:12–18:08:40 UTC+7**, tổng **148,05 s**, load model **29,82 s**. Không gồm tải model/cài dependencies. [requirements-lock](../../starter/requirements-lock.txt) lưu toàn bộ library; không random split, không khóa seed nội bộ HNSW.

## Cấu hình và benchmark

| Strategy | Chunking | Metadata/filter |
|---|---|---|
| A | Fixed 500 ký tự, overlap 50; không vượt unit nguồn | Metadata đầy đủ, không filter |
| B | Gom paragraph/heading trong unit, max 1000 ký tự; đoạn quá dài cắt tại ranh giới whitespace trong giới hạn | Metadata giống A, không filter |
| C | Cùng IDs/text/span/embedding như B | Chỉ áp filter khai báo trong question; câu còn lại không filter |

A–B chỉ thay chunking. B–C chỉ thay query filtering; dữ liệu/model/store/metric/gold giữ nguyên. Dùng cùng model encode riêng mỗi cấu hình để đo ingest; không dùng cache embedding của cấu hình trước. Heading được giữ như đoạn ngắn, không có parser cây heading Sphinx chuyên dụng.

[20 câu và gold](../../benchmark/questions.json) được soạn/xác minh **trước retrieval**, khóa bằng hash và thời điểm trong [freeze.json](../../benchmark/freeze.json). Q01–Q15 dev, Q16–Q20 test. Có trực tiếp, diễn đạt lại, điều kiện/ngoại lệ và metadata; Q02/Q05/Q15/Q19/Q20 có filter từ tên chương ngay trong question, trong đó hai câu test. Không đưa answer/gold source/page vào model query hoặc where. Chia theo chủ đề câu hỏi, không document-disjoint; có nguy cơ chia sẻ từ vựng giữa dev/test.

Mỗi câu có id/split/question/expected_answer/gold_source_id/gold_page/evidence_quote/filter/category/alternative_gold. Evidence được kiểm tra sau NFC và gộp whitespace trên đúng source unit. Hỗ trợ gold thay thế đã khai báo; không tự thêm gold sau khi xem điểm. Bộ này chưa liệt kê mọi bằng chứng tương đương trên toàn corpus, nên metric có thể bảo thủ. Không câu unanswerable trong chỉ số bắt buộc.

Tiêu chí chọn chốt trước test: ưu tiên **dev Evidence Hit@3**, tiếp theo dev Hit@1; hòa thì B→C→A (B đơn giản hơn C, vẫn giữ cấu trúc). [selection.json](../../results/selection.json) được ghi lúc **18:08:40,389 UTC+7**, với **0 test query đã chạy**, chọn **B**; sau đó mới đánh giá test. Không chỉnh benchmark/chunk/model từ điểm test.

Hit bắt buộc = có **một chunk** trong top-k đúng source/page và chứa đủ evidence sau chuẩn hóa; không lấy hợp các chunk làm metric chính. Mỗi trace giữ diagnostic evidence_split_across_chunks khi không chunk đã ingest nào chứa đủ quote; không tự coi đúng page là hit.

## Kết quả

| Strategy | Split | Hit@1 (n/N) | Evidence Hit@3 (n/N) | Chunk count | Ingest (s) | API USD |
|---|---|---:|---:|---:|---:|---:|
| A | dev | 8/15 | 9/15 | 456 | 44,33 | 0 |
| A | test | 4/5 | 4/5 | 456 | 44,33 | 0 |
| B | dev | 9/15 | 13/15 | 256 | 33,64 | 0 |
| B | test | 4/5 | 5/5 | 256 | 33,64 | 0 |
| C | dev | 9/15 | 13/15 | 256 | 33,02 | 0 |
| C | test | 4/5 | 5/5 | 256 | 33,02 | 0 |

Thời gian ingest là một lần đo cho mỗi cấu hình, lặp ở hai dòng split để tiện đối chiếu, không phải đo riêng dev/test. Bao gồm chunk/embed/upsert, không gồm model load và lần upsert kiểm tra thứ hai. Reload A/B/C **2,24/1,63/1,40 s**, số chunk giữ **456/256/256**. Không chạy nhiều lần để ước lượng phương sai; cache hệ thống và thứ tự chạy ảnh hưởng thời gian.

| Strategy | Coherence mean /2 (n) | Metadata đủ+đúng (n/N) | Tuân thủ phạm vi filter test | Grounding 0/1/2 (số câu), mean /2 |
|---|---:|---:|---:|---|
| A | 1,1 (10) | 15/15 | 1/2, không bật filter | 1/0/4; 1,6 |
| B | 1,7 (10) | 15/15 | 2/2, không bật filter | 0/0/5; 2,0 |
| C | 1,7 (10) | 15/15 | 2/2, bật filter | 0/0/5; 2,0 |

**Bảng audit là nhãn do Codex đọc/chấm, chưa phải xác nhận chấm thủ công của tác giả.** [Phương pháp và bias](../../results/AUDIT.md), [coherence labels](../../results/coherence_labels.csv), [grounding labels](../../results/grounding_labels.csv), [metadata labels](../../results/metadata_labels.csv), [filter audit](../../results/filter_audit.csv), [audit summary](../../results/audit_summary.json). Tác giả chưa review, có [phiếu trống](../../results/author_review_pending.csv) để điền tên/điểm/lý do/ngày thật; không tự nhận đã có human audit.

Coherence dùng cùng 10 unit classes:001–010, vị trí midpoint đã chốt trước retrieval; JSON mẫu kèm source_text, anchor và chunk. Grounding đọc đủ Q16–20 top-3 mỗi cấu hình, không suy từ Hit@3; C không filter có cùng hits B và đã đối chiếu. Metadata kiểm tra đủ source/page/section của 45 hit so nguồn và verify offset; không phát hiện lỗi metadata. Không mặc định filter 100%: A/Q20 rank 3 thuộc stdlib thay vì stdlib2. B đạt 2/2 tình cờ trên test nhỏ; C áp điều kiện thực tế. Tổng dev+test filter: A 3/5, B 3/5, C 5/5.

Trace: [traces.jsonl](../../results/traces.jsonl), **60 truy vấn cấu hình × top-3 =180 hit**, gồm question/gold/evidence, chunk ID/text/cosine score/metadata, filter, nhãn hit và diagnostic. [Metrics CSV](../../results/metrics.csv), [statistics](../../results/statistics.json), [config/version](../../results/run.json), [experiment log](../../artifacts/experiment_log.csv), [errors.log](../../results/errors.log). errors.log rỗng vì pipeline thành công; lỗi hạ tầng đầu phiên được ghi riêng [environment_log](../../results/environment_log.json).

## Phân tích và kết luận

A→B: dev Hit@3 tăng **9→13/15**, test **4→5/5**, coherence AI **1,1→1,7/2**; metadata cùng **15/15**. B ít hơn **200 chunk (43,9%)**, tổng ký tự chunk **186.056** thay **204.937** (A overlap), token trước truncate **48.467** thay **53.856**. Độ dài min/median/mean/p95/max: A **52/500/449,42/500/500**, B/C **103/813/726,78/988/1000**. Ingest B thấp hơn trong lần đo này, không kết luận tốc độ tổng quát.

B→C: Hit@1/Hit@3 và audit test không đổi; chunk/vector/storage giống nhau. C giữ đúng phạm vi cả **5/5** câu filter so B **3/5**, loại nguồn ngoài chương mà chưa đổi evidence hit. Query search time tổng 20 câu A/B/C **0,154/0,135/0,149 s**, quá nhỏ/một lần để kết luận chênh hiệu năng. C thêm giả định có metadata user input đúng; input sai hoặc quá hẹp có thể bỏ mất nguồn phù hợp.

Ví dụ lỗi và đánh đổi:

1. **A/Q02 — controlflow:003**: quote phải gồm điều kiện break và ngoại lệ return/exception. A tách quote qua cửa sổ nên không một chunk nào đủ; B/C giữ quote và hit top-1. Điều này chứng minh phải xét đủ evidence, không chỉ source/page.
2. **A/Q18 — classes:014**: top-1 nói double-underscore mangling, bỏ lỡ đoạn “không có enforced private instance variables” và quy ước _spam. B/C gom đúng đoạn, Hit@1 và grounding=2; A grounding=0. Đây là lỗi thật trên câu test, không sửa cấu hình sau khi xem.
3. **B/Q16 — classes:009**: B giữ đủ định nghĩa nhưng ở rank 2, còn A có ở rank 1. B cải thiện Hit@3 tổng thể nhưng không thắng mọi thứ hạng.
4. **B/C Q01 — controlflow:003**: tìm về else/break thay vì câu định nghĩa “innermost enclosing”. Chunk chứa gold tồn tại nhưng không vào top-3, nên chunking tốt hơn vẫn có lỗi ranking. **Q11** còn cho thấy gold quote hẹp có thể không chấp nhận diễn đạt tương đương từ classes:003; không thay gold sau test, ghi giới hạn annotation.

Chọn **B** theo dev rule đã chốt: Hit@3 ngang C, không cần metadata input và ít chunk hơn A. Khi sản phẩm bắt buộc giới hạn chương/version thì **C** phù hợp vì thực thi phạm vi, ngay cả khi Hit@3 không tăng. Kết luận chỉ áp dụng corpus/benchmark nhỏ này.

Hạn chế lớn: **45/256 chunk B/C vượt 256 token**, encoder truncate phần cuối dù Chroma lưu nguyên văn; có thể ảnh hưởng ranking khi evidence nằm cuối. A không chunk nào vượt giới hạn. Không thay tham số đã chốt sau khi xem test; lần sau thử token-aware chunking/model dài hơn trên dev và benchmark holdout mới. Coherence sample chỉ một chương, gold chưa bao phủ mọi equivalent source, câu hỏi tiếng Anh, chỉ 5 test và hai câu filter test, nhãn do AI đồng thời làm code và benchmark, không blind/inter-rater. Không kiểm tra corpus khác hay tiếng Việt. Chi phí/thời gian chỉ một máy/một lần; không tính download/điện/khấu hao.

Grounding ở đây là **độ đủ evidence retrieval**, không chạy generation và không phải độ đúng đáp án LLM. B/C 5/5 không có nghĩa hoàn hảo hoặc tốt nhất tổng quát.

Cải tiến có kiểm soát: thêm người chấm độc lập, tác giả review đủ phiếu; mở rộng test theo tài liệu/phiên bản độc lập và alternative evidence; token-aware boundaries, parser Sphinx thực, thử model context dài; đo nhiều lần, kiểm tra recall exact/filter. Hybrid BM25 là mở rộng tùy chọn, chưa dùng để tạo các bảng baseline này.

Thử nghiệm phụ hybrid: sau khi baseline/test đã khóa, mình tạo 5 câu holdout mới và khóa trước khi chạy hybrid. Grid dense weight 0/.25/.5/.75/1 chọn weight 0 trên dev với 15/15 Hit@3; holdout đạt hybrid 4/5 Hit@3 và dense 4/5, nhưng hybrid làm mất Hit@3 ở H04. Đây là minh họa có kiểm soát, dùng lại dev để chọn tham số và không thay kết quả A/B/C; xem [summary](../../results/hybrid/summary.json).

## Công cụ AI và trạng thái nộp bài

Codex hỗ trợ viết code, soạn benchmark, chạy thí nghiệm, đọc trace, dự thảo nhãn audit và báo cáo. Kiểm tra bằng checksum upstream/model, evidence validation, bốn unit test (normalization/provenance/complete evidence/aggregation), actual-vector persistence/update/filter tests và [submission verification](../../results/submission_verification.json). Không bịa số liệu, nguồn, log hoặc tự nhận tác giả đã chấm nhãn. Tác giả cần hiểu code và review nhãn trước nộp.

Repo/commit và việc nộp link theo giảng viên: xem [STUDENT.md](../../STUDENT.md) và [checklist thực tế](../../artifacts/task_checklist.md). Chưa có URL repo/kênh nộp được người dùng cung cấp, không tự nhận đã push/mở quyền/nộp hoặc suy deadline từ checkpoint.
