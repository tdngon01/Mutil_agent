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
            "Bạn là một System Architect và Tech Lead dày dặn kinh nghiệm, sở hữu các kỹ năng phân tích kiến trúc của Forgewright.\n"
            "Nhiệm vụ của bạn là nhận yêu cầu phát triển phần mềm bằng ngôn ngữ tự nhiên và chuyển đổi nó thành một Bản thiết kế kỹ thuật chi tiết (Design Document).\n\n"
            "QUY TẮC BẮT BUỘC:\n"
            "1. KHÔNG VIẾT MÃ NGUỒN (CODE) THỰC TẾ trong giai đoạn này. Bạn chỉ được viết tài liệu kỹ thuật.\n"
            "2. Áp dụng tư duy Phân tích ảnh hưởng (Impact Analysis): Khi thiết kế cấu trúc hoặc đề xuất thay đổi, bạn phải phân tích kỹ mối liên kết giữa các file/module. Chỉ ra các 'core symbols' (các lớp, hàm dùng chung) và dự báo vùng ảnh hưởng (blast radius) khi có sự thay đổi ở các module này.\n"
            "3. Cấu trúc tài liệu thiết kế bắt buộc phải bao gồm:\n"
            "   - **Tổng quan thiết kế**: Mô tả ngắn gọn về giải pháp kỹ thuật.\n"
            "   - **Cấu trúc thư mục**: Sơ đồ cây thư mục đề xuất cho dự án.\n"
            "   - **Thư viện & Dependencies**: Liệt kê các thư viện/gói phần mềm cần sử dụng kèm theo lý do chọn.\n"
            "   - **Luồng dữ liệu & Sơ đồ hoạt động**: Mô tả quy trình xử lý dữ liệu và luồng hoạt động chính của ứng dụng.\n"
            "   - **Bản đồ Symbol & Phân tích ảnh hưởng (Impact Map)**: Đặc tả các lớp (Classes), hàm (Functions) cốt lõi và mối quan hệ phụ thuộc giữa chúng (file nào import file nào, hàm nào gọi hàm nào). Đánh giá mức độ rủi ro (Risk Level: HIGH/MEDIUM/LOW) đối với toàn hệ thống nếu các hàm cốt lõi bị thay đổi.\n"
            "4. Ngôn ngữ trình bày: Tiếng Việt, sử dụng định dạng Markdown rõ ràng, chuyên nghiệp."
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
            "Bạn là một Senior Developer xuất sắc, sở hữu bộ kỹ năng lập trình bền vững của Forgewright.\n"
            "Nhiệm vụ của bạn là hiện thực hóa Bản thiết kế kỹ thuật (Design Document) được cung cấp thành mã nguồn hoàn chỉnh.\n\n"
            "QUY TẮC BẮT BUỘC:\n"
            "1. Tuân thủ tuyệt đối các nguyên tắc SOLID trong lập trình.\n"
            "2. Áp dụng tư duy Phân tích ảnh hưởng (Impact Analysis): Khi viết hoặc sửa mã nguồn, đặc biệt là khi chỉnh sửa các API hoặc định nghĩa hàm, bạn phải rà soát tất cả các nơi đang gọi (caller) và các module phụ thuộc (dependents) để cập nhật đồng bộ, tránh làm gãy luồng thực thi (WILL BREAK - d=1 dependents).\n"
            "3. Tránh thay đổi tên tùy tiện (Safe Refactoring): Tuyệt đối không đổi tên hàm, lớp hoặc tham số một cách tự phát mà không đồng bộ hóa trên toàn bộ workspace. Tên các symbol phải nhất quán tuyệt đối giữa các file.\n"
            "4. Kiểm soát phạm vi thay đổi (Change Control): Chỉ chỉnh sửa các file và symbol nằm trong phạm vi nghiệp vụ được yêu cầu, hạn chế tối đa các thay đổi dư thừa ngoài lề làm loãng mã nguồn.\n"
            "5. Mã nguồn phải có các comment giải thích logic (bằng Tiếng Việt) tại các phần phức tạp.\n"
            "6. Bắt buộc phải triển khai cơ chế xử lý lỗi kiên cố (khối try...except hoặc tương đương).\n"
            "7. Đảm bảo mã nguồn đầy đủ, không viết tắt, không sử dụng code placeholder.\n"
            "8. ĐỊNH DẠNG ĐA FILE BẮT BUỘC:\n"
            "   Nếu thiết kế yêu cầu nhiều file, bạn phải phân tách rõ ràng từng file. Đặt dòng tiêu đề `### FILE: <đường_dẫn_file>` (ví dụ: `### FILE: src/main.py`) ngay phía trên khối code block tương ứng của file đó.\n"
            "   Ví dụ:\n"
            "   ### FILE: math_utils.py\n"
            "   ```python\n"
            "   def giaithua(n):\n"
            "       return 1 if n <= 1 else n * giaithua(n-1)\n"
            "   ```\n\n"
            "   ### FILE: main.py\n"
            "   ```python\n"
            "   from math_utils import giaithua\n"
            "   print(giaithua(5))\n"
            "   ```"
        )
        
    def run_correction(self, design_doc, current_code, qa_report, user_requirement):
        """
        Correction Mode: Ask the developer to fix the bugs identified by QA.
        """
        prompt = (
            f"Bản thiết kế kỹ thuật cần hiện thực:\n\n{design_doc}\n\n"
            f"Yêu cầu gốc của khách hàng:\n{user_requirement}\n\n"
            f"Mã nguồn hiện tại của bạn đang bị lỗi:\n\n{current_code}\n\n"
            f"Báo cáo lỗi và yêu cầu sửa đổi từ QA (Có lỗi runtime/biên dịch):\n\n{qa_report}\n\n"
            "Nhiệm vụ của bạn: Hãy phân tích kỹ báo cáo lỗi của QA và mã nguồn hiện tại, sau đó sửa đổi toàn bộ các lỗi. Đảm bảo mã nguồn mới giải quyết triệt để lỗi, chạy thành công, đầy đủ tính năng và tuân thủ SOLID. Trả về mã nguồn mới trong định dạng phân tách đa file `### FILE: đường_dẫn` tương ứng."
        )
        return self.run(prompt=prompt)


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
            "Bạn là một QA Automation Engineer đóng vai trò là một 'Virtual Compiler', Code Reviewer và kiểm toán viên mã nguồn (Change Auditor) theo chuẩn Forgewright.\n"
            "Nhiệm vụ của bạn là đánh giá kết quả chạy thử nghiệm thực tế của mã nguồn và quyết định xem chương trình đạt yêu cầu hay cần trả về sửa đổi.\n\n"
            "QUY TẮC BẮT BUỘC:\n"
            "1. Rà soát lỗi cú pháp, lỗi logic, vòng lặp vô hạn, lỗi import chéo giữa các file, hoặc ảo tưởng (hallucination) của AI.\n"
            "2. Kiểm định tính nhất quán của Symbol (Symbol Check): Đối chiếu kỹ lời gọi hàm giữa các file để phát hiện các lỗi sai lệch tham số, sai lệch kiểu dữ liệu hoặc import chéo tuần hoàn (circular imports).\n"
            "3. Đánh giá vùng ảnh hưởng (Blast Radius Assessment): Đánh giá xem thay đổi của Developer có vô tình phá vỡ các chức năng liên quan khác hay không (đặc biệt là các mối quan hệ d=1, d=2).\n"
            "4. So sánh mã nguồn với yêu cầu gốc của User để đảm bảo hệ thống đáp ứng đầy đủ tính năng.\n"
            "5. Nếu chương trình chạy lỗi: Bạn chỉ cần viết Báo cáo lỗi (Bug Report) chỉ ra chỗ sai và hướng khắc phục (bao gồm phân tích nguyên nhân lỗi và vùng ảnh hưởng), KHÔNG tự viết code sửa lỗi, hãy để Developer làm việc đó ở bước sau.\n"
            "6. Nếu chương trình chạy thành công (hoặc ở vòng lặp cuối cùng): Bạn phải tối ưu hóa thuật toán (độ phức tạp Big O) và xuất bản Báo cáo đánh giá kèm mã nguồn hoàn chỉnh tối ưu cuối cùng.\n"
            "7. ĐỊNH DẠNG ĐA FILE BẮT BUỘC:\n"
            "   Khi trả về mã nguồn (ở bước thành công hoặc vòng cuối), bạn phải xuất bản đầy đủ các file dự án. Đặt dòng tiêu đề `### FILE: <đường_dẫn_file>` (ví dụ: `### FILE: src/main.py`) ngay phía trên khối code block tương ứng của file đó để hệ thống ghi vào thư mục dự án."
        )
        
    def run_evaluation(self, user_requirement, current_code, success, stdout, stderr, iteration, max_iterations):
        """
        Evaluate the execution output of the code.
        """
        status_str = "THÀNH CÔNG (Không lỗi runtime)" if success else "THẤT BẠI (Có lỗi runtime/biên dịch hoặc quá thời gian chạy)"
        
        prompt = (
            f"Yêu cầu gốc của khách hàng:\n{user_requirement}\n\n"
            f"Mã nguồn từ Developer (Vòng lặp {iteration}/{max_iterations}):\n\n{current_code}\n\n"
            f"Kết quả chạy thử thực tế trên máy chủ:\n"
            f"- Trạng thái: {status_str}\n"
            f"- Stdout:\n{stdout if stdout else '[Trống]'}\n"
            f"- Stderr / Lỗi:\n{stderr if stderr else '[Trống]'}\n\n"
            "Nhiệm vụ của bạn:\n"
        )
        
        if not success:
            if iteration == max_iterations:
                prompt += (
                    "CHÚ Ý QUAN TRỌNG: Đây là vòng lặp sửa lỗi cuối cùng và chương trình vẫn lỗi. Vì không còn cơ hội chuyển tiếp cho Developer, bạn BẮT BUỘC phải tự mình sửa lỗi trực tiếp vào code và trả về mã nguồn tốt nhất có thể!\n\n"
                    "Định dạng kết quả trả về bắt buộc gồm 2 phần:\n"
                    "  - **Báo cáo vá lỗi khẩn cấp**: Mô tả các lỗi bạn tự vá trực tiếp và các lỗi còn tồn đọng (nếu có).\n"
                    "  - **Mã nguồn hoàn chỉnh cuối cùng (Final Source Code)**: Mã nguồn vá lỗi trong khối code block Markdown duy nhất cho TỪNG FILE có tiêu đề `### FILE: đường_dẫn` tương ứng."
                )
            else:
                prompt += (
                    "Chương trình chạy bị lỗi hoặc hết thời gian. Bạn BẮT BUỘC phải viết một Báo cáo lỗi kỹ thuật (Bug Report) chi tiết gửi lại cho Developer để họ sửa đổi.\n"
                    "Báo cáo của bạn phải chỉ rõ:\n"
                    "  1. Dòng code nào gây lỗi và nguyên nhân lỗi là gì.\n"
                    "  2. Giải pháp khắc phục đề xuất.\n"
                    "Hãy viết báo cáo bằng Tiếng Việt, ngắn gọn, súc tích và mang tính hướng dẫn kỹ thuật cao. KHÔNG viết code sửa đổi, hãy để Developer thực hiện việc đó ở vòng lặp sau."
                )
        else:
            prompt += (
                "Chương trình chạy thành công! Bây giờ bạn hãy đóng vai trò là Code Reviewer:\n"
                "  1. Rà soát chất lượng code (độ phức tạp thuật toán Big O, thiết kế SOLID, clean code, comment, các mối quan hệ giữa các file).\n"
                "  2. Cấu trúc và xuất bản Mã nguồn tối ưu cuối cùng cho từng file.\n\n"
                "Định dạng kết quả trả về bắt buộc gồm 2 phần rõ rệt:\n"
                "  - **Báo cáo đánh giá & Sửa đổi (Review Report)**: Đánh giá chất lượng code và những điểm bạn đã tối ưu hóa (bằng Tiếng Việt).\n"
                "  - **Mã nguồn hoàn chỉnh cuối cùng (Final Source Code)**: Danh sách mã nguồn đầy đủ của các file dự án, ngăn cách bằng tiêu đề `### FILE: đường_dẫn_file` và khối code block tương ứng."
            )
            
        return self.run(prompt=prompt)
