# Benchmark đã chốt

20 câu tiếng Anh từ Python Tutorial 3.13.0: Q01–Q15 dev, Q16–Q20 test. Câu hỏi được soạn trước lần retrieval đầu tiên; evidence được đối chiếu văn bản nguồn rồi khóa bằng SHA-256 trong [freeze.json](freeze.json). [questions.json](questions.json) giữ answer, source, page ID, evidence, loại câu và filter.

Không chia ngẫu nhiên: test giữ các chủ đề câu hỏi riêng (class variables, finally, private convention, thread coordination, logging). Các chương vẫn xuất hiện ở cả hai split; không coi là kiểm tra độc lập theo tài liệu. Bộ nhỏ, tiếng Anh và cùng tác giả soạn gold có nguy cơ thiên lệch.

Filter có từ ngữ cảnh ngay trong câu hỏi: Q02 controlflow, Q05 datastructures, Q15 errors, Q19/Q20 stdlib2. Trường section lấy từ tên chapter upstream; không lọc document_id, page, gold source hoặc answer. C chạy không filter với 15 câu còn lại. A/B không áp dụng filter.

Chọn bằng dev Evidence Hit@3, tiếp theo dev Hit@1. Hòa thì ưu tiên B, C, A (B không cần filter mà vẫn giữ cấu trúc). Ghi selection.json trước khi chạy test; không chỉnh tham số từ điểm test.

Hit bắt buộc: một chunk thuộc source/page gold và chứa nguyên evidence sau NFC + gộp whitespace. Không gộp nhiều chunk cho metric chính. Alternative gold được hỗ trợ và chỉ ghi khi đã kiểm chứng; benchmark này không liệt kê bằng chứng tương đương chưa được xác minh. Vì vậy metric là phép đo bảo thủ, có thể bỏ sót cách diễn đạt tương đương.

Mẫu coherence: 10 page ID đầu theo thứ tự từ điển (classes:001–classes:010), vị trí giữa đơn vị; chọn chunk có start nhỏ nhất chứa vị trí đó, giống nhau A/B/C. Grounding: đọc đủ 5 test × top-3 × 3 cấu hình. Metadata: 45 bản ghi test top-3 so với source/page/section thật. Nhãn AI và nhãn tác giả phải được phân biệt; không biến string match thành nhãn thủ công.
