import re
import os
import shutil
import time
import zipfile
import io
from executor import execute_workspace

class SharedContext:
    def __init__(self, user_requirement):
        self.user_requirement = user_requirement
        self.design_doc = ""
        self.raw_code = ""
        self.final_review = ""
        self.execution_history = [] 
        self.files = {}            
        self.zip_data = None       


class Orchestrator:
    def __init__(self, architect_agent, developer_agent, qa_agent):
        self.architect = architect_agent
        self.developer = developer_agent
        self.qa = qa_agent

    def run_architect(self, user_requirement, feedback=None, previous_design=None, search_context=None):
        """
        Executes Architect Agent. Supports revising the design based on user feedback and appending search_context.
        """
        if feedback and previous_design:
            prompt = (
                f"Yêu cầu gốc của khách hàng:\n{user_requirement}\n\n"
                f"Bản thiết kế kỹ thuật hiện tại của bạn:\n\n{previous_design}\n\n"
                f"Feedback yêu cầu chỉnh sửa từ khách hàng:\n\n{feedback}\n\n"
                "Nhiệm vụ của bạn: Hãy phân tích feedback và cập nhật lại Bản thiết kế kỹ thuật (Design Document). KHÔNG viết code thực tế. Xuất ra bản thiết kế mới định dạng Markdown."
            )
        else:
            prompt = user_requirement
            if search_context:
                prompt += f"\n\n[Tài liệu tham khảo tra cứu trực tuyến từ Web]:\n\n{search_context}"
        return self.architect.run(prompt=prompt)

    def run_developer(self, design_doc, user_requirement, feedback=None, previous_code=None, search_context=None):
        """
        Executes Developer Agent. Supports revising the code based on user feedback and appending search_context.
        """
        if feedback and previous_code:
            prompt = (
                f"Bản thiết kế kỹ thuật:\n\n{design_doc}\n\n"
                f"Yêu cầu gốc của khách hàng:\n{user_requirement}\n\n"
                f"Mã nguồn hiện tại của bạn:\n\n{previous_code}\n\n"
                f"Feedback yêu cầu chỉnh sửa từ khách hàng:\n\n{feedback}\n\n"
                "Nhiệm vụ của bạn: Hãy phân tích kỹ feedback của khách hàng và sửa đổi mã nguồn. Trả về toàn bộ mã nguồn mới trong cấu trúc phân tách đa file `### FILE: đường_dẫn` tương ứng."
            )
        else:
            prompt = (
                f"Bản thiết kế kỹ thuật cần hiện thực:\n\n{design_doc}\n\n"
                f"Yêu cầu gốc của khách hàng để đối chiếu:\n{user_requirement}"
            )
            if search_context:
                prompt += f"\n\n[Tài liệu tham khảo tra cứu trực tuyến từ Web]:\n\n{search_context}"
        return self.developer.run(prompt=prompt)

    def run_qa_loop(self, design_doc, raw_code_input, user_requirement, status_callback=None, search_context=None):
        """
        Executes the Developer-QA feedback loop with real execution and packages ZIP output.
        Appends web search context to instructions for better correction.
        """
        # Append search context to user requirement for QA evaluation
        user_req_with_search = user_requirement
        if search_context:
            user_req_with_search += f"\n\n[Tài liệu tham khảo tra cứu trực tuyến từ Web]:\n\n{search_context}"
            
        context = SharedContext(user_requirement)
        context.design_doc = design_doc
        context.raw_code = raw_code_input
        max_iterations = 3
        
        current_dir = os.path.dirname(os.path.abspath(__file__))
        workspace_dir = os.path.join(current_dir, f"workspace_{int(time.time())}_{random_string(5)}")
        os.makedirs(workspace_dir, exist_ok=True)
        
        try:
            current_code_input = raw_code_input
            
            for i in range(1, max_iterations + 1):
                loop_label = f"Vòng {i}/{max_iterations}"
                
                # Parse files
                files_dict = self._parse_files_with_fallback(current_code_input)
                context.files = files_dict
                
                # Clear and write workspace
                self._clear_directory(workspace_dir)
                self._write_files_to_dir(workspace_dir, files_dict)
                
                if status_callback:
                    status_callback("qa_start", f"🛡️ [QA Engineer] ({loop_label}) Đang chạy thử nghiệm dự án...", None)
                    
                # Run execution check
                success, stdout, stderr, exit_code = execute_workspace(workspace_dir)
                
                exec_entry = {
                    "iteration": i,
                    "success": success,
                    "stdout": stdout,
                    "stderr": stderr,
                    "exit_code": exit_code
                }
                context.execution_history.append(exec_entry)
                
                if status_callback:
                    status_callback("loop_exec_log", f"🛡️ [QA Engineer] ({loop_label}) Kết quả chạy thử nghiệm.", exec_entry)
                    
                # Run QA evaluation
                try:
                    qa_report = self.qa.run_evaluation(
                        user_requirement=user_req_with_search,
                        current_code=current_code_input,
                        success=success,
                        stdout=stdout,
                        stderr=stderr,
                        iteration=i,
                        max_iterations=max_iterations
                    )
                except Exception as e:
                    if status_callback:
                        status_callback("qa_error", f"❌ Lỗi ở bước QA Engineer ({loop_label}): {str(e)}", None)
                    raise e
                    
                if success:
                    # Success
                    context.final_review = qa_report
                    qa_files = self._parse_multi_files(qa_report)
                    if qa_files:
                        context.files.update(qa_files)
                        self._write_files_to_dir(workspace_dir, qa_files)
                        
                    if status_callback:
                        status_callback("qa_end", f"🛡️ [QA Engineer] ({loop_label}) Kiểm thử THÀNH CÔNG! Đã phê duyệt và tối ưu hóa dự án.", context.final_review)
                    break
                else:
                    # Failed
                    if i == max_iterations:
                        context.final_review = qa_report
                        qa_files = self._parse_multi_files(qa_report)
                        if qa_files:
                            context.files.update(qa_files)
                            self._write_files_to_dir(workspace_dir, qa_files)
                            
                        if status_callback:
                            status_callback("qa_end", f"🛡️ [QA Engineer] ({loop_label}) Kiểm thử THẤT BẠI. QA đã tiến hành tự vá lỗi trực tiếp.", context.final_review)
                    else:
                        # Bug correction
                        if status_callback:
                            status_callback("developer_start", f"💻 [Senior Developer] ({loop_label}) Đang tiến hành sửa đổi mã nguồn dựa trên báo cáo của QA...", qa_report)
                            
                        try:
                            current_code_input = self.developer.run_correction(
                                design_doc=context.design_doc,
                                current_code=current_code_input,
                                qa_report=qa_report,
                                user_requirement=user_req_with_search
                            )
                        except Exception as e:
                            if status_callback:
                                status_callback("developer_error", f"❌ Lỗi ở bước Developer sửa lỗi ({loop_label}): {str(e)}", None)
                            raise e
                            
                        if status_callback:
                            status_callback("developer_end", f"💻 [Senior Developer] ({loop_label}) Đã sửa lỗi và cập nhật mã nguồn.", current_code_input)
            
            # Pack ZIP
            context.zip_data = self._zip_directory(workspace_dir)
            
        finally:
            # Clean up
            self._clear_directory(workspace_dir)
            if os.path.exists(workspace_dir):
                try:
                    os.rmdir(workspace_dir)
                except Exception:
                    pass
                    
        return context

    def _parse_multi_files(self, text):
        pattern = r"###\s*[Ff]ile:\s*([^\n]+)\n```(?:\w+)?\n(.*?)\n```"
        matches = re.findall(pattern, text, re.DOTALL)
        files = {}
        for filepath, content in matches:
            files[filepath.strip()] = content.strip()
        return files

    def _parse_files_with_fallback(self, text):
        files = self._parse_multi_files(text)
        if not files:
            pattern = r"```(\w+)?\n(.*?)\n```"
            matches = re.findall(pattern, text, re.DOTALL)
            if matches:
                best_match = max(matches, key=lambda m: len(m[1]))
                lang = best_match[0] or "txt"
                code = best_match[1]
                
                ext_map = {
                    "python": ".py", "py": ".py",
                    "javascript": ".js", "js": ".js",
                    "typescript": ".ts", "ts": ".ts",
                    "html": ".html", "css": ".css"
                }
                ext = ext_map.get(lang.lower(), ".txt")
                files[f"main{ext}"] = code.strip()
        return files

    def _write_files_to_dir(self, dir_path, files_dict):
        for rel_path, content in files_dict.items():
            rel_path = rel_path.replace("\\", "/").strip().lstrip("/")
            abs_path = os.path.abspath(os.path.join(dir_path, rel_path))
            
            if not abs_path.startswith(os.path.abspath(dir_path)):
                continue
                
            os.makedirs(os.path.dirname(abs_path), exist_ok=True)
            with open(abs_path, "w", encoding="utf-8") as f:
                f.write(content)

    def _clear_directory(self, dir_path):
        if os.path.exists(dir_path):
            for filename in os.listdir(dir_path):
                file_path = os.path.join(dir_path, filename)
                try:
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.unlink(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                except Exception:
                    pass

    def _zip_directory(self, dir_path):
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for root, dirs, files in os.walk(dir_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, dir_path)
                    zip_file.write(file_path, arcname)
        zip_buffer.seek(0)
        return zip_buffer.getvalue()


def random_string(length=5):
    import random
    import string
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(length))
