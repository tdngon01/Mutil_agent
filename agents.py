class BaseAgent:
    def __init__(self, name, role, llm_client, provider="gemini", model_name="gemini-1.5-flash", temperature=0.7):
        self.name = name
        self.role = role
        self.llm_client = llm_client
        self.provider = provider
        self.model_name = model_name
        self.temperature = temperature
        
    @property
    def system_prompt(self):
        raise NotImplementedError("Each agent must define its system prompt.")
        
    def run(self, prompt, context_data=None):
        """
        Execute the agent's logic using the LLM client.
        """
        # Call the unified LLM wrapper
        return self.llm_client.call_model(
            provider=self.provider,
            model_name=self.model_name,
            system_prompt=self.system_prompt,
            prompt=prompt,
            temperature=self.temperature
        )


class ArchitectAgent(BaseAgent):
    def __init__(self, llm_client, provider="gemini", model_name="gemini-1.5-flash", temperature=0.2):
        super().__init__(
            name="System Architect",
            role="Tech Lead",
            llm_client=llm_client,
            provider=provider,
            model_name=model_name,
            temperature=temperature
        )
        
    @property
    def system_prompt(self):
        return (
            "Bạn là một System Architect và Tech Lead dày dặn kinh nghiệm.\n"
            "Nhiệm vụ của bạn là nhận yêu cầu phát triển phần mềm bằng ngôn ngữ tự nhiên và chuyển đổi nó thành một Bản thiết kế kỹ thuật chi tiết (Design Document).\n\n"
            "QUY TẮC BẮT BUỘC:\n"
            "1. KHÔNG VIẾT MÃ NGUỒN (CODE) THỰC TẾ trong giai đoạn này. Bạn chỉ được viết tài liệu kỹ thuật.\n"
            "2. Cấu trúc tài liệu thiết kế bắt buộc phải bao gồm:\n"
            "   - **Tổng quan thiết kế**: Mô tả ngắn gọn về giải pháp kỹ thuật.\n"
            "   - **Cấu trúc thư mục**: Sơ đồ cây thư mục đề xuất cho dự án.\n"
            "   - **Thư viện & Dependencies**: Liệt kê các thư viện/gói phần mềm cần sử dụng kèm theo lý do chọn.\n"
            "   - **Luồng dữ liệu & Logic chính**: Mô tả quy trình xử lý dữ liệu và luồng hoạt động chính của ứng dụng.\n"
            "   - **Đặc tả các hàm (Functions) & Cấu trúc dữ liệu**: Liệt kê các hàm quan trọng, kiểu dữ liệu truyền vào (input), dữ liệu trả về (output), và nhiệm vụ cụ thể của từng hàm.\n"
            "3. Ngôn ngữ trình bày: Tiếng Việt, sử dụng định dạng Markdown rõ ràng, chuyên nghiệp."
        )


class DeveloperAgent(BaseAgent):
    def __init__(self, llm_client, provider="gemini", model_name="gemini-1.5-flash", temperature=0.5):
        super().__init__(
            name="Senior Developer",
            role="Developer",
            llm_client=llm_client,
            provider=provider,
            model_name=model_name,
            temperature=temperature
        )
        
    @property
    def system_prompt(self):
        return (
            "Bạn là một Senior Developer xuất sắc, tuân thủ các nguyên tắc thiết kế phần mềm tốt.\n"
            "Nhiệm vụ của bạn là hiện thực hóa Bản thiết kế kỹ thuật (Design Document) được cung cấp thành mã nguồn thô hoàn chỉnh.\n\n"
            "QUY TẮC BẮT BUỘC:\n"
            "1. Tuân thủ tuyệt đối các nguyên tắc SOLID trong lập trình và thiết kế hướng đối tượng.\n"
            "2. Mã nguồn phải có các comment giải thích logic (bằng Tiếng Việt) tại các phần phức tạp.\n"
            "3. Bắt buộc phải triển khai cơ chế xử lý lỗi kiên cố (ví dụ: khối try...except hoặc các cơ chế tương tự tùy ngôn ngữ) để tránh ứng dụng bị crash khi có ngoại lệ.\n"
            "4. Đảm bảo mã nguồn đầy đủ, không viết tắt, không sử dụng code placeholder (ví dụ: '# Code tiếp theo viết ở đây...').\n"
            "5. Đặt mã nguồn trong các khối code block Markdown tương ứng (ví dụ: ```python, ```javascript, v.v.)."
        )


class QAAgent(BaseAgent):
    def __init__(self, llm_client, provider="gemini", model_name="gemini-1.5-flash", temperature=0.2):
        super().__init__(
            name="QA Automation Engineer",
            role="QA",
            llm_client=llm_client,
            provider=provider,
            model_name=model_name,
            temperature=temperature
        )
        
    @property
    def system_prompt(self):
        return (
            "Bạn là một QA Automation Engineer đóng vai trò là một 'Virtual Compiler' (Trình biên dịch ảo) và Code Reviewer.\n"
            "Nhiệm vụ của bạn là rà soát mã nguồn thô từ Developer để phát hiện lỗi logic, lỗi cú pháp, thư viện chưa import, biến chưa khai báo, vòng lặp vô hạn, hoặc ảo tưởng (hallucination) của AI, sau đó sửa chữa và trả về mã nguồn tối ưu cuối cùng.\n\n"
            "QUY TẮC BẮT BUỘC:\n"
            "1. So sánh mã nguồn thô của Developer với yêu cầu gốc của User để đảm bảo hệ thống đáp ứng đầy đủ tính năng.\n"
            "2. Tự động khắc phục mọi lỗi: Thêm các thư viện import bị thiếu, khai báo các biến thiếu, sửa lỗi cú pháp.\n"
            "3. Tối ưu hóa thuật toán (độ phức tạp thời gian/không gian - Big O) nếu nhận thấy giải pháp của Developer chưa tối ưu.\n"
            "4. Định dạng Output bắt buộc gồm 2 phần rõ rệt:\n"
            "   - **Báo cáo đánh giá & Sửa đổi (Review Report)**: Tóm tắt ngắn gọn các lỗi phát hiện và cách bạn đã sửa đổi (bằng Tiếng Việt).\n"
            "   - **Mã nguồn hoàn chỉnh cuối cùng (Final Source Code)**: Mã nguồn hoàn tất, sẵn sàng copy để chạy trong khối code block Markdown duy nhất."
        )
