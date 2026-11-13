# Corpus và quyền sử dụng

Chủ đề: quy tắc và cách dùng Python trong Python Tutorial **CPython v3.13.0**, tám chương controlflow, datastructures, modules, inputoutput, errors, classes, stdlib, stdlib2. Đây là tài liệu hướng dẫn kỹ thuật, tiếng Anh.

[manifest.json](manifest.json) liệt kê URL, đường dẫn raw, hash SHA-256, thời điểm truy cập thực, snapshot, số ký tự và toàn bộ đơn vị nguồn. [pages.jsonl](pages.jsonl) là đầu vào pipeline. Không có số trang PDF; page là ID đơn vị text tương đương theo GUIDE.

93 đơn vị không chồng lặp, mỗi đơn vị ≥1.500 ký tự NFC chuẩn hóa. Đi theo thứ tự chương, cắt tại ranh giới đoạn sau ≥1.800 ký tự; phần cuối <1.500 ký tự được nhập vào đơn vị trước. start/end là khoảng nửa mở [start,end) trên chapter .txt. Không nhân bản; overlap chỉ xuất hiện ở chunk A sau bước đếm corpus. Không lấy bìa, mục lục hoặc trang chỉ references. Không có scan và không dùng OCR.

Nguồn gốc: https://github.com/python/cpython/tree/v3.13.0/Doc/tutorial
Quyền: Python software và documentation theo PSF License Version 2. Examples, recipes và code trong documentation còn được dual-license Zero-Clause BSD từ Python 3.8.6; không áp giấy phép này cho toàn bộ prose. Giữ nguyên [LICENSE.txt](python_tutorial/LICENSE.txt) và [documentation-license.rst](python_tutorial/documentation-license.rst), bao gồm copyright © 2001–2024 Python Software Foundation.

Thay đổi so với upstream: giữ raw .rst; tạo bản normalized .txt bằng NFC, chuẩn newline/khoảng trắng, bỏ target/index/directive markup; giữ heading, signature method và code indentation. Một số Sphinx cross-reference/markup còn lại và ranh giới đơn vị có thể cắt ngữ cảnh: xem giới hạn trong báo cáo.

Tái tạo từ root bằng Python trong venv:

    starter/.venv/Scripts/python.exe starter/scripts/prepare_data.py

Script dùng raw đã lưu nếu có; chỉ tải file thiếu. Đối chiếu checksum manifest trước khi thay snapshot. Không chạy lại build_benchmark.py để chỉnh benchmark đã xem test.

Model không commit trọng số: download_model.py tải 90,9 MB safetensors cùng tokenizer/config từ commit cố định trong model_manifest.json (Apache-2.0 theo model card). Manifest ghi hash từng file; chạy validation trước ingest. Model không chứa dữ liệu cá nhân của bài.
