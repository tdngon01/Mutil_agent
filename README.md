# 🤖 Multi-Agent Auto-Coding Lab

Hệ thống Đa tác tử Phối hợp Tự động Lập trình (Multi-Agent Auto-Coding Lab) được thiết kế theo mô hình Kiến trúc 3 lớp với luồng xử lý tuần tự (Sequential Pipeline) qua 3 Agent: **System Architect (Tech Lead)**, **Senior Developer**, và **QA Automation Engineer**. Dự án sử dụng **Streamlit** làm giao diện frontend tương tác và gọi API của **Google Gemini** và **Groq** để xử lý logic.

---

## 📐 Kiến trúc & Luồng Hoạt động (Sequence Flow)

1. **User Input**: Người dùng nhập yêu cầu phần mềm và khóa API (Gemini/Groq) qua giao diện Web.
2. **System Architect (Tech Lead)**: Nhận yêu cầu thô và xuất bản tài liệu thiết kế kỹ thuật (Design Document) dạng Markdown (không viết code).
3. **Senior Developer**: Nhận bản thiết kế kỹ thuật và tiến hành lập trình mã nguồn thô (Raw Code) đầy đủ, tuân thủ SOLID và có try-except bảo vệ.
4. **QA Automation Engineer**: Rà soát mã nguồn thô, tự động sửa các lỗi cú pháp/logic/biến thiếu/import thiếu và tối ưu thuật toán. Xuất ra mã nguồn hoàn chỉnh (Final Code) và báo cáo đánh giá (Review Report).
5. **Output**: Giao diện hiển thị kết quả chi tiết của từng Agent dưới dạng tab và cho phép tải mã nguồn về máy chỉ với một click.

---

## 📁 Cấu trúc Thư mục

```text
multi_agent_auto_coding_lab/
├── .venv/                 # Môi trường ảo Python (Virtual Environment)
├── requirements.txt      # Khai báo thư viện (streamlit, google-generativeai, requests, python-dotenv)
├── llm.py                # Wrapper gọi API Gemini/Groq + cơ chế Exponential Backoff
├── agents.py             # Định nghĩa các Class Agent (Architect, Developer, QA)
├── orchestrator.py       # Quản lý luồng chạy tuần tự giữa các Agent
└── app.py                # Frontend Web bằng Streamlit
```

---

## 🚀 Hướng dẫn Cài đặt & Chạy ứng dụng

### 1. Chuẩn bị Môi trường
Yêu cầu máy tính cài đặt sẵn **Python 3.8** trở lên (Khuyên dùng Python 3.10+).

Mở terminal hoặc command prompt tại thư mục này và thực hiện các bước sau:

```bash
# Tạo môi trường ảo (Nếu chưa tạo)
python -m venv .venv

# Kích hoạt môi trường ảo (Windows)
.venv\Scripts\activate

# Kích hoạt môi trường ảo (macOS/Linux)
source .venv/bin/activate
```

### 2. Cài đặt các thư viện cần thiết
```bash
pip install -r requirements.txt
```

### 3. Khởi chạy Ứng dụng Web
```bash
streamlit run app.py
```

Ứng dụng sẽ tự động mở trong trình duyệt của bạn tại địa chỉ mặc định: [http://localhost:8501](http://localhost:8501).

---

## ⚙️ Các tính năng nổi bật

- **Xử lý lỗi kiên cố (Fault-tolerant)**: Ứng dụng tích hợp cơ chế *Exponential Backoff* tự động thử lại khi API bị Rate Limit (Lỗi 429) hoặc dịch vụ quá tải tạm thời (Lỗi 503).
- **Log thời gian thực trực quan**: Sử dụng `st.status()` cập nhật động tiến độ làm việc của từng tác tử riêng biệt ngay trên UI giúp người dùng dễ dàng theo dõi.
- **Tải file nhanh**: Trình phân tách code tự động nhận diện ngôn ngữ lập trình của mã nguồn cuối cùng và xuất file tải xuống tương ứng (`.py`, `.js`, `.ts`, `.html`, v.v.).
