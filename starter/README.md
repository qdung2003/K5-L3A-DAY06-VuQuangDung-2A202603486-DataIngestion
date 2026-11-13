# Starter — pipeline đã hiện thực với Chroma

Phương án chạy bài này: **Sentence Transformers local + Chroma PersistentClient**, không cần Docker/API key. Xem [README root](../README.md) để setup và chạy lại. Python đã chạy: 3.13.15.

~~~powershell
# Từ root, sau khi tạo starter/.venv và cài requirements:
starter/.venv/Scripts/python.exe starter/scripts/download_model.py
starter/.venv/Scripts/python.exe starter/scripts/check_setup.py
cd starter
.venv/Scripts/python.exe -m src.run --output ../results/rerun_01
.venv/Scripts/python.exe -m unittest discover -s tests -v
~~~

Các hàm ingestion, chunking, embeddings, store, evaluation và run đã hiện thực. src/store.py dùng ChromaStore thay khung PgVectorStore. Corpus/benchmark chính ở ../data và ../benchmark; kết quả lần nộp ở ../results. Không dùng starter/data hoặc chroma_db cũ làm corpus/kết quả.

- Model tải vào ../.cache/all-MiniLM-L6-v2, revision/hash trong ../data/model_manifest.json.
- Chroma tạo vector_store với ba collection day06_a/b/c, cosine HNSW search_ef=100.
- Nạp full snapshot sẽ upsert ID ổn định rồi xóa ID cũ ngoài snapshot; không chạy đồng thời nhiều writer. Đây không phải atomic multi-collection transaction; nếu bị ngắt, chạy lại cùng snapshot.
- Filter section/version/language là trường string cho phép; dùng API where của Chroma, không ghép SQL.
- errors.log lưu exception đầy đủ, không in .env hay key.

## Phương án PostgreSQL gốc (tùy chọn, chưa dùng để báo cáo)

Các file docker-compose.yml/init.sql được giữ để tham khảo. Nếu chọn PostgreSQL thay Chroma cần tự hiện thực adapter tương ứng và chạy lại thí nghiệm; không lấy kết quả Chroma gán cho PostgreSQL.

~~~powershell
cd starter
python -m venv .venv
.venv/Scripts/Activate.ps1
pip install -r requirements.txt
if (!(Test-Path .env)) { Copy-Item .env.example .env }
docker compose -p day6_student_starter up -d --wait
python scripts/check_setup.py --backend postgres
~~~

Cổng mặc định 127.0.0.1:55433; nếu bận, sửa cả docker-compose.yml và DATABASE_URL trong .env. init.sql chỉ chạy trên volume mới; kiểm tra extension/log trước khi thay dữ liệu. Không xóa volume chứa dữ liệu để chữa lỗi. Dừng container và giữ volume bằng docker compose -p day6_student_starter stop.

.env là local-only, được ignore; model local không cần key. Lần đầu cần mạng tải thư viện/model. requirements.txt pin thư viện chính, requirements-lock.txt ghi toàn bộ môi trường thực tế.
