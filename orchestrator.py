class SharedContext:
    def __init__(self, user_requirement):
        self.user_requirement = user_requirement
        self.design_doc = ""
        self.raw_code = ""
        self.final_review = ""


class Orchestrator:
    def __init__(self, architect_agent, developer_agent, qa_agent):
        self.architect = architect_agent
        self.developer = developer_agent
        self.qa = qa_agent

    def run_pipeline(self, user_requirement, status_callback=None):
        """
        Executes the sequential multi-agent coding pipeline:
        Architect (Tech Lead) -> Developer (Senior Developer) -> QA (QA Engineer).
        Updates state in real-time via the status_callback.
        """
        context = SharedContext(user_requirement)
        
        # --- PHASE 1: System Architect (Tech Lead) ---
        if status_callback:
            status_callback("architect_start", "📐 [System Architect] Bắt đầu thiết kế kiến trúc hệ thống...", None)
            
        try:
            context.design_doc = self.architect.run(prompt=context.user_requirement)
        except Exception as e:
            if status_callback:
                status_callback("architect_error", f"❌ Lỗi ở bước System Architect: {str(e)}", None)
            raise e
            
        if status_callback:
            status_callback("architect_end", "📐 [System Architect] Đã hoàn thành bản thiết kế chi tiết.", context.design_doc)

        # --- PHASE 2: Senior Developer ---
        if status_callback:
            status_callback("developer_start", "💻 [Senior Developer] Bắt đầu lập trình mã nguồn thô dựa trên bản thiết kế...", None)
            
        dev_prompt = (
            f"Bản thiết kế kỹ thuật cần hiện thực:\n\n{context.design_doc}\n\n"
            f"Yêu cầu gốc của khách hàng để đối chiếu:\n{context.user_requirement}"
        )
        
        try:
            context.raw_code = self.developer.run(prompt=dev_prompt)
        except Exception as e:
            if status_callback:
                status_callback("developer_error", f"❌ Lỗi ở bước Senior Developer: {str(e)}", None)
            raise e
            
        if status_callback:
            status_callback("developer_end", "💻 [Senior Developer] Đã viết xong mã nguồn thô.", context.raw_code)

        # --- PHASE 3: QA Automation Engineer ---
        if status_callback:
            status_callback("qa_start", "🛡️ [QA Engineer] Bắt đầu rà soát code, sửa lỗi logic/cú pháp và tối ưu hóa...", None)
            
        qa_prompt = (
            f"Yêu cầu gốc của khách hàng:\n{context.user_requirement}\n\n"
            f"Mã nguồn thô từ Developer:\n\n{context.raw_code}"
        )
        
        try:
            context.final_review = self.qa.run(prompt=qa_prompt)
        except Exception as e:
            if status_callback:
                status_callback("qa_error", f"❌ Lỗi ở bước QA Engineer: {str(e)}", None)
            raise e
            
        if status_callback:
            status_callback("qa_end", "🛡️ [QA Engineer] Đã rà soát xong và xuất mã nguồn tối ưu cuối cùng.", context.final_review)

        return context
