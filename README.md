# Day 06 — Python Tutorial ingestion benchmark

Bài cá nhân **Vũ Quang Dũng — 2A202603486 — L3A**. Pipeline Python đã chạy thực tế trên 8 chương Python Tutorial **3.13.0**: **93 đơn vị nguồn**, **20 câu (15 dev / 5 test)**, ba cấu hình A/B/C, semantic embedding local và Chroma lưu trên đĩa.

| Cấu hình | Dev Hit@1 | Dev Evidence Hit@3 | Test Hit@1 | Test Evidence Hit@3 | Chunk |
|---|---:|---:|---:|---:|---:|
| A: fixed 500, overlap 50 | 8/15 | 9/15 | 4/5 | 4/5 | 456 |
| B: paragraph ≤1000 | 9/15 | 13/15 | 4/5 | 5/5 | 256 |
| C: B + filter khi có input | 9/15 | 13/15 | 4/5 | 5/5 | 256 |

**B được chọn trên dev trước khi truy vấn test**, theo [quy tắc đã khóa](benchmark/freeze.json) và [selection.json](results/selection.json). Không suy rộng từ 5 câu test.

## Chạy lại trên Windows PowerShell

Python 3.11–3.14 theo yêu cầu lab; môi trường đã chạy là **3.13.15 / Windows 11 / CPU 4 threads**. Dependency lock ghi đúng môi trường thực tế; Python/platform khác có thể cần bản wheel tương thích và phải ghi thay đổi. Lần đầu cần mạng để cài thư viện và tải model khoảng 92 MB; corpus đã kèm repo.

Từ root:

~~~powershell
python -m venv starter/.venv
& starter/.venv/Scripts/Activate.ps1
python -m pip install -r starter/requirements.txt
# Hoặc toàn bộ dependency chính xác của lần chạy:
# python -m pip install -r starter/requirements-lock.txt
if (!(Test-Path starter/.env)) { Copy-Item starter/.env.example starter/.env }
$env:PYTHONUTF8 = '1'
python starter/scripts/download_model.py
python starter/scripts/check_setup.py
cd starter
python -m src.run --output ../results/rerun_01
python -m unittest discover -s tests -v
~~~

Không cần activate nếu dùng đường dẫn đầy đủ tới starter/.venv/Scripts/python.exe. Linux/macOS dùng starter/.venv/bin/python và source starter/.venv/bin/activate.

check_setup.py mặc định kiểm tra **Chroma + corpus + model**, in Setup OK; không có nghĩa là đã hoàn thành audit. Chroma tạo starter/vector_store với day06_a, day06_b, day06_c. Mọi lệnh chạy lại ghi thư mục output mới, giữ nguyên lần nộp trong results/. Rerun dùng cùng frozen corpus/benchmark; không chỉnh test sau khi xem điểm.

Đã chọn **Chroma**, vì vậy Docker/PostgreSQL không nằm trên đường chạy này. Máy hiện chưa có Docker; không tuyên bố đã cài/chạy Docker. Nếu chủ động chuyển sang starter PostgreSQL, xem [hướng dẫn gốc](starter/README.md), dùng docker compose -p day6_student_starter up -d --wait và python scripts/check_setup.py --backend postgres; đó là phương án khác, chưa phải backend thí nghiệm đã báo cáo.

Không cần API key. .env đã có local và được ignore; không in/commit nội dung. Model/backend lỗi sẽ raise và ghi errors.log, không fallback sang mock.

## Dữ liệu, model và kiểm chứng

- [Manifest corpus](data/manifest.json), [quyền và tái tạo](data/README.md), [đơn vị nguồn](data/pages.jsonl): nguồn upstream v3.13.0, PSF License, code examples còn dual-license 0BSD. Mỗi đơn vị ≥1.500 ký tự chuẩn hóa, không trùng/overlap. Có raw, normalized và ranh giới [start,end).
- [Benchmark](benchmark/questions.json) và [thiết kế](benchmark/README.md): evidence đều được xác minh trong nguồn; section lấy từ tên chương. Năm câu có input filter, hai câu thuộc test. Query chỉ chứa question; C chỉ nhận filter khai báo trước.
- Model **sentence-transformers/all-MiniLM-L6-v2**, revision **1110a243fdf4706b3f48f1d95db1a4f5529b4d41**, **384 chiều**, mean pooling, L2 normalize, cosine. Query/document dùng cùng tokenizer và model, không prefix. [Model manifest + hash](data/model_manifest.json). Model card lưu trong cache tải về, license Apache-2.0.
- **Chroma 1.5.9 PersistentClient**, approximate HNSW cosine, search_ef=100. Native where lọc metadata; không đảm bảo recall exact hoặc thứ hạng giống mọi lần build. Khi filter hẹp cần kiểm tra số hit và recall; trace lần này đủ top-3.
- Chi phí API **0 USD**; chưa định giá điện/phần cứng/mạng. Lần chạy **13/11/2026, 18:06:12–18:08:40 (UTC+7)**; tổng **148,05 s**, load model **29,82 s**, ingest A/B/C **44,33 / 33,64 / 33,02 s**. Download/cài dependency không nằm trong thời gian đó. [Thông số và version](results/run.json), [thống kê ký tự/token](results/statistics.json), [nhật ký A/B/C](artifacts/experiment_log.csv).
- Không random split; HNSW internal randomness không được khóa seed. Lần nạp lại không nhân đôi: **456→456, 256→256, 256→256**; [kiểm tra độc lập bằng process mới](results/storage_verification.json) còn xác minh đổi snapshot xóa chunk cũ.
- B/C có **45/256 chunk vượt max_seq_length=256**: embedding bị truncate nhưng văn bản chunk lưu đầy đủ. Đây là hạn chế của cấu hình đã chốt, không sửa bằng điểm test.

Để kiểm tra đầu vào/model hash:

~~~powershell
cd starter
python -m src.run --validate-only
cd ..
python starter/scripts/verify_store.py
python starter/scripts/verify_submission.py
~~~

verify_store.py dùng vector neural thật đã lưu, kiểm tra bền vững sau khi process pipeline kết thúc, reload idempotent, thay snapshot và từ chối đầu vào sai. Không dùng vector giả.

## Hồ sơ kết quả và audit

[Trace đầy đủ](results/traces.jsonl) có **60 lượt × top-3 = 180 hit**, text/ID/score/metadata/gold/evidence. [Metrics](results/metrics.csv) tách dev/test. [Báo cáo cá nhân](report/individual/2A202603486_VuQuangDung.md) phân tích năm khía cạnh, hai ví dụ lỗi và đánh đổi.

Các nhãn [coherence](results/coherence_labels.csv), [grounding](results/grounding_labels.csv), [metadata](results/metadata_labels.csv) do **Codex đọc mẫu và chấm, chưa phải tác giả chấm thủ công**. Có lý do từng nhãn và [phương pháp](results/AUDIT.md); không suy nhãn định tính từ hit/string match. Tác giả cần rà soát [phiếu review](results/author_review_pending.csv) trước khi xác nhận yêu cầu audit thủ công. Không tự gán tên tác giả vào nhãn AI.

[Checklist 58 mục](artifacts/task_checklist.md) chỉ rõ mục đã làm, phương án thay thế, mục cần tác giả và phần ngoài workspace. [STUDENT.md](STUDENT.md) ghi trạng thái repo/commit; [SUBMISSION.md](SUBMISSION.md) giữ nguyên hướng dẫn và có đối chiếu thực tế.

Công cụ AI: Codex hỗ trợ code, benchmark, chạy lệnh, đọc trace và dự thảo nhãn/báo cáo. Kiểm tra bằng hash nguồn/model, unit tests, trace đối chiếu nguồn và kiểm thử lưu trữ. Chưa có người chấm độc lập; không gọi nhãn AI là audit con người, không gọi grounding là độ đúng câu trả lời LLM.

## Hybrid tùy chọn

Sau khi baseline/test đã khóa, thử nghiệm holdout mới với RRF + BM25 được khóa trong benchmark/hybrid_freeze.json. Dev chọn dense weight 0 với 15/15 Hit@3; holdout hybrid đạt 4/5 Hit@3, dense 4/5 và có một regression H04. Kết quả phụ không thay A/B/C.
