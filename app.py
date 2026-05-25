import streamlit as st
import re
import os
import time
from llm import LLMClient
from agents import ArchitectAgent, DeveloperAgent, QAAgent
from orchestrator import Orchestrator
from search import generate_search_context

# Set up page configurations
st.set_page_config(
    page_title="Multi-Agent Auto-Coding Lab",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for modern styling
st.markdown("""
<style>
    .main-header {
        font-family: 'Inter', sans-serif;
        font-weight: 800;
        background: linear-gradient(135deg, #6C63FF, #3F3D56);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-family: 'Inter', sans-serif;
        font-weight: 400;
        color: #6C757D;
        margin-bottom: 2rem;
    }
    .agent-title {
        color: #6C63FF;
        font-weight: 700;
        font-size: 1.3rem;
        margin-top: 1rem;
        margin-bottom: 0.5rem;
    }
    .stButton>button {
        background: linear-gradient(135deg, #6C63FF, #5A52E5);
        color: white;
        border: none;
        padding: 0.6rem 2rem;
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(108, 99, 255, 0.3);
    }
    .review-gate {
        padding: 1.5rem;
        border-radius: 12px;
        background-color: #F0F2F6;
        border-left: 5px solid #FF4B4B;
        margin-bottom: 1.5rem;
    }
</style>
""", unsafe_allow_html=True)

# --- INITIALIZE STATEFUL VARIABLES ---
if "pipeline_step" not in st.session_state:
    st.session_state.pipeline_step = "idle"
if "user_requirement" not in st.session_state:
    st.session_state.user_requirement = ""
if "design_doc" not in st.session_state:
    st.session_state.design_doc = ""
if "raw_code" not in st.session_state:
    st.session_state.raw_code = ""
if "files" not in st.session_state:
    st.session_state.files = {}
if "final_review" not in st.session_state:
    st.session_state.final_review = ""
if "zip_data" not in st.session_state:
    st.session_state.zip_data = None
if "execution_history" not in st.session_state:
    st.session_state.execution_history = []
if "search_context" not in st.session_state:
    st.session_state.search_context = ""


# --- SIDEBAR CONFIGURATIONS ---
st.sidebar.markdown("# ⚙️ Cấu hình Lab")

# API Keys Configuration
st.sidebar.subheader("🔑 API Keys & Gateways")
gemini_key = st.sidebar.text_input(
    "Google Gemini Key",
    type="password",
    value=os.getenv("GEMINI_API_KEY", ""),
    help="Lấy API Key từ Google AI Studio"
)
groq_key = st.sidebar.text_input(
    "Groq Key",
    type="password",
    value=os.getenv("GROQ_API_KEY", ""),
    help="Lấy API Key từ Groq Console"
)
openai_key = st.sidebar.text_input(
    "OpenAI Key",
    type="password",
    value=os.getenv("OPENAI_API_KEY", ""),
    help="Lấy API Key từ OpenAI Platform"
)
anthropic_key = st.sidebar.text_input(
    "Anthropic Key",
    type="password",
    value=os.getenv("ANTHROPIC_API_KEY", ""),
    help="Lấy API Key từ Anthropic Console"
)
tavily_key = st.sidebar.text_input(
    "Tavily Search Key (Tùy chọn)",
    type="password",
    value=os.getenv("TAVILY_API_KEY", ""),
    help="Lấy API Key từ Tavily (https://tavily.com/) để tìm kiếm ổn định không bị chặn bởi Captcha"
)


# Custom API Setup
st.sidebar.markdown("---")
st.sidebar.subheader("🔌 Custom Endpoint (Ollama/OpenRouter...)")
custom_url = st.sidebar.text_input(
    "Base API Endpoint URL",
    value="",
    placeholder="Ví dụ: http://localhost:11434/v1/chat/completions",
    help="Địa chỉ POST REST endpoint tương thích chuẩn OpenAI"
)
custom_key = st.sidebar.text_input(
    "Custom API Key / Token",
    type="password",
    value="",
    help="Khóa bảo mật hoặc Bearer Token cho Custom Endpoint (nếu có)"
)

# Web Search Toggle
st.sidebar.markdown("---")
st.sidebar.subheader("🔍 Tìm kiếm trực tuyến")
enable_search = st.sidebar.checkbox(
    "Kích hoạt Web Search", 
    value=True,
    help="Tự động tìm kiếm tài liệu (API Documentation) trên DuckDuckGo cho các thư viện liên quan trước khi thiết kế/lập trình."
)

# Helper function to get model selection elements
def configure_agent_model(agent_label, prefix_id):
    st.sidebar.subheader(agent_label)
    
    provider = st.sidebar.selectbox(
        f"Nhà cung cấp [{prefix_id}]",
        ["Gemini", "Groq", "OpenAI", "Anthropic", "Custom"],
        key=f"provider_{prefix_id}"
    )
    
    models_dict = {
        "Gemini": ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-2.0-flash-exp", "gemini-1.0-pro", "Custom Model..."],
        "Groq": ["llama-3.3-70b-versatile", "llama-3.1-70b-versatile", "llama3-70b-8192", "llama3-8b-8192", "mixtral-8x7b-32768", "gemma2-9b-it", "Custom Model..."],
        "OpenAI": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-4", "gpt-3.5-turbo", "o1-mini", "o1-preview", "Custom Model..."],
        "Anthropic": ["claude-3-5-sonnet-latest", "claude-3-5-haiku-latest", "claude-3-opus-latest", "claude-3-sonnet-20240229", "claude-3-haiku-20240307", "Custom Model..."],
        "Custom": ["Custom Model..."]
    }
    
    model_option = st.sidebar.selectbox(
        f"Mô hình [{prefix_id}]",
        models_dict[provider],
        key=f"model_opt_{prefix_id}"
    )
    
    if model_option == "Custom Model...":
        model_name = st.sidebar.text_input(
            f"Điền tên Model tùy chỉnh [{prefix_id}]",
            value="",
            placeholder="Ví dụ: qwen-2.5-coder",
            key=f"custom_name_{prefix_id}"
        )
    else:
        model_name = model_option
        
    temp = st.sidebar.slider(
        f"Nhiệt độ (Temperature) [{prefix_id}]", 
        0.0, 1.0, 
        0.2 if prefix_id in ["1", "3"] else 0.5, 
        0.1,
        key=f"temp_{prefix_id}"
    )
    
    return provider, model_name, temp

st.sidebar.markdown("---")
st.sidebar.markdown("## 🤖 Cấu hình từng Tác tử")

arch_provider, arch_model, arch_temp = configure_agent_model("📐 Agent 1: System Architect", "1")
st.sidebar.markdown("---")
dev_provider, dev_model, dev_temp = configure_agent_model("💻 Agent 2: Senior Developer", "2")
st.sidebar.markdown("---")
qa_provider, qa_model, qa_temp = configure_agent_model("🛡️ Agent 3: QA Engineer", "3")


# --- CORE AGENTS INITIALIZATION HELPER ---
def get_orchestrator():
    final_arch_model = st.session_state.get("custom_name_1", "").strip() if arch_model == "Custom Model..." else arch_model
    final_dev_model = st.session_state.get("custom_name_2", "").strip() if dev_model == "Custom Model..." else dev_model
    final_qa_model = st.session_state.get("custom_name_3", "").strip() if qa_model == "Custom Model..." else qa_model
    
    llm_client = LLMClient(
        gemini_api_key=gemini_key, 
        groq_api_key=groq_key,
        openai_api_key=openai_key,
        anthropic_api_key=anthropic_key,
        custom_api_key=custom_key,
        custom_api_url=custom_url
    )
    
    architect = ArchitectAgent(
        llm_client=llm_client, 
        provider=arch_provider, 
        model_name=final_arch_model, 
        temperature=arch_temp
    )
    developer = DeveloperAgent(
        llm_client=llm_client, 
        provider=dev_provider, 
        model_name=final_dev_model, 
        temperature=dev_temp
    )
    qa = QAAgent(
        llm_client=llm_client, 
        provider=qa_provider, 
        model_name=final_qa_model, 
        temperature=qa_temp
    )
    
    return Orchestrator(architect, developer, qa)


# --- LOG PLACEHOLDERS ---
search_status_box = st.empty()
architect_box = st.empty()
developer_box = st.empty()
qa_status_box = st.empty()

# Custom callback function to handle real-time pipeline status updates
def update_status(event_type, message, data=None):
    # Web Search logs
    if event_type == "search_queries_start":
        st.session_state.search_status_element = search_status_box.status(message, expanded=True)
    elif event_type == "search_exec_start":
        with st.session_state.search_status_element:
            st.markdown(message)
    elif event_type == "search_queries_end":
        st.session_state.search_status_element.update(label="✅ " + message, state="complete", expanded=False)
        if data:
            with st.session_state.search_status_element:
                st.markdown(data)
    elif event_type == "search_error":
        st.session_state.search_status_element.update(label=message, state="error", expanded=True)

    # Architect logs
    elif event_type == "architect_start":
        st.session_state.arch_status = architect_box.status(message, expanded=True)
    elif event_type == "architect_end":
        st.session_state.arch_status.update(label="✅ " + message, state="complete", expanded=False)
        with st.session_state.arch_status:
            st.markdown(data)
    elif event_type == "architect_error":
        st.session_state.arch_status.update(label=message, state="error", expanded=True)

# QA logs
def update_qa_status(event_type, message, data=None):
    if event_type == "qa_start":
        st.session_state.qa_status_element = qa_status_box.status(message, expanded=True)
    elif event_type == "qa_end":
        st.session_state.qa_status_element.update(label="✅ " + message, state="complete", expanded=False)
        with st.session_state.qa_status_element:
            st.markdown(data)
    elif event_type == "qa_error":
        st.session_state.qa_status_element.update(label=message, state="error", expanded=True)
    elif event_type == "developer_start":
        st.session_state.dev_status_element = qa_status_box.status(message, expanded=True)
        if data:
            with st.session_state.dev_status_element:
                st.markdown("**Báo cáo lỗi từ QA:**")
                st.markdown(data)
    elif event_type == "developer_end":
        st.session_state.dev_status_element.update(label="✅ " + message, state="complete", expanded=False)
        with st.session_state.dev_status_element:
            st.code(data)
    elif event_type == "loop_exec_log":
        it = data["iteration"]
        success = data["success"]
        stdout = data["stdout"]
        stderr = data["stderr"]
        exit_code = data["exit_code"]
        
        with st.session_state.qa_status_element:
            st.markdown(f"**📍 [Vòng thử nghiệm {it}] Đang chạy thử nghiệm dự án...**")
            if success:
                st.success(f"✔️ Biên dịch & Chạy thành công (Exit Code: {exit_code})")
                if stdout:
                    with st.expander(f"Xem Output dòng lệnh (Vòng {it})"):
                        st.code(stdout)
            else:
                st.error(f"❌ Chạy thất bại (Exit Code: {exit_code})")
                if stderr:
                    st.markdown("**Chi tiết lỗi (Traceback/Compiler error):**")
                    st.code(stderr)
                if stdout:
                    with st.expander(f"Xem Output dòng lệnh trước khi lỗi (Vòng {it})"):
                        st.code(stdout)


# --- DYNAMIC STEP-BY-STEP RENDERING ---

# Step 0: IDLE STATE
if st.session_state.pipeline_step == "idle":
    st.subheader("💡 Nhập yêu cầu phát triển phần mềm")
    user_req_input = st.text_area(
        "Mô tả chi tiết những gì bạn muốn hệ thống lập trình:",
        height=150,
        placeholder="Ví dụ: Thiết kế hệ thống đa file gồm config.py và main.py tính toán giai thừa..."
    )
    
    if st.button("🚀 Khởi chạy hệ thống tác tử", use_container_width=True):
        selected_providers = {arch_provider, dev_provider, qa_provider}
        missing_keys = []
        if "Gemini" in selected_providers and not gemini_key.strip():
            missing_keys.append("Google Gemini Key")
        if "Groq" in selected_providers and not groq_key.strip():
            missing_keys.append("Groq Key")
        if "OpenAI" in selected_providers and not openai_key.strip():
            missing_keys.append("OpenAI Key")
        if "Anthropic" in selected_providers and not anthropic_key.strip():
            missing_keys.append("Anthropic Key")
        if "Custom" in selected_providers and not custom_url.strip():
            missing_keys.append("Custom Base API Endpoint URL")
            
        if not user_req_input.strip():
            st.error("Vui lòng nhập yêu cầu của bạn.")
        elif missing_keys:
            st.error(f"❌ Thiếu cấu hình/khóa API cho các nhà cung cấp được lựa chọn: {', '.join(missing_keys)}")
        else:
            # Create Orchestrator
            try:
                orchestrator = get_orchestrator()
                
                # 1. OPTIONAL WEB SEARCH TRAVERSAL
                if enable_search:
                    final_arch_model = st.session_state.get("custom_name_1", "").strip() if arch_model == "Custom Model..." else arch_model
                    search_context = generate_search_context(
                        llm_client=orchestrator.architect.llm_client,
                        user_requirement=user_req_input,
                        provider=arch_provider,
                        model_name=final_arch_model,
                        tavily_api_key=tavily_key,
                        status_callback=update_status
                    )
                    st.session_state.search_context = search_context
                else:
                    st.session_state.search_context = ""
                
                # 2. RUN ARCHITECT DESIGN STEP
                with st.spinner("📐 System Architect (Tech Lead) đang thiết kế cấu trúc hệ thống..."):
                    design = orchestrator.run_architect(
                        user_requirement=user_req_input,
                        search_context=st.session_state.search_context
                    )
                    st.session_state.design_doc = design
                    st.session_state.user_requirement = user_req_input
                    st.session_state.pipeline_step = "review_design"
                    st.rerun()
            except Exception as e:
                st.error(f"Lỗi khi chạy thiết kế kiến trúc: {e}")

# Step 1: REVIEW DESIGN GATE
elif st.session_state.pipeline_step == "review_design":
    st.info(f"📋 **Yêu cầu gốc**: {st.session_state.user_requirement}")
    if st.session_state.search_context:
        with st.expander("🔍 Xem tài liệu đã tra cứu trực tuyến từ Web"):
            st.markdown(st.session_state.search_context)
            
    st.markdown("<div class='review-gate'><h3>📐 Chốt chặn 1: Kiểm duyệt & Chỉnh sửa Thiết kế (Design Approval Gate)</h3>"
                "<p>Bản thiết kế kỹ thuật từ System Architect hiển thị bên dưới. Bạn có thể sửa trực tiếp nội dung hoặc nhập feedback yêu cầu thiết kế lại.</p></div>", unsafe_allow_html=True)
    
    edited_design = st.text_area(
        "📝 Biên tập tài liệu thiết kế (Markdown):", 
        value=st.session_state.design_doc, 
        height=350
    )
    
    design_feedback = st.text_input(
        "🔄 Ý kiến đóng góp / Yêu cầu thiết kế lại (nếu có):", 
        placeholder="Ví dụ: Thiết kế thêm file database.py để lưu dữ liệu bài viết..."
    )
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Đồng ý thiết kế & Tiến hành lập trình ➡️", use_container_width=True):
            st.session_state.design_doc = edited_design
            st.session_state.pipeline_step = "run_developer"
            st.rerun()
            
    with col2:
        if st.button("Thiết kế lại dựa trên feedback 🔄", use_container_width=True):
            if not design_feedback.strip():
                st.warning("Vui lòng điền ý kiến đóng góp trước khi yêu cầu thiết kế lại.")
            else:
                try:
                    orchestrator = get_orchestrator()
                    with st.spinner("📐 System Architect đang thiết kế lại..."):
                        new_design = orchestrator.run_architect(
                            st.session_state.user_requirement,
                            feedback=design_feedback,
                            previous_design=st.session_state.design_doc,
                            search_context=st.session_state.search_context
                        )
                        st.session_state.design_doc = new_design
                        st.success("Đã hoàn thành thiết kế lại!")
                        time.sleep(1)
                        st.rerun()
                except Exception as e:
                    st.error(f"Lỗi khi thiết kế lại: {e}")

# Transition step: Run Developer
elif st.session_state.pipeline_step == "run_developer":
    st.info("💻 Đang xử lý...")
    try:
        orchestrator = get_orchestrator()
        with st.spinner("💻 Senior Developer đang lập trình dựa trên bản thiết kế đã duyệt..."):
            raw_code = orchestrator.run_developer(
                design_doc=st.session_state.design_doc,
                user_requirement=st.session_state.user_requirement,
                search_context=st.session_state.search_context
            )
            st.session_state.raw_code = raw_code
            st.session_state.files = orchestrator._parse_files_with_fallback(raw_code)
            st.session_state.pipeline_step = "review_code"
            st.rerun()
    except Exception as e:
        st.error(f"Lỗi khi lập trình mã nguồn: {e}")
        if st.button("Quay lại"):
            st.session_state.pipeline_step = "review_design"
            st.rerun()

# Step 2: REVIEW CODE GATE
elif st.session_state.pipeline_step == "review_code":
    st.info(f"📋 **Yêu cầu gốc**: {st.session_state.user_requirement}")
    with st.expander("📐 Xem Bản thiết kế kỹ thuật đã duyệt"):
        st.markdown(st.session_state.design_doc)
        
    st.markdown("<div class='review-gate'><h3>💻 Chốt chặn 2: Kiểm duyệt & Chỉnh sửa Mã nguồn (Code Approval Gate)</h3>"
                "<p>Xem trước và biên tập code thô do Developer viết trước khi gửi sang kiểm thử tự động của QA.</p></div>", unsafe_allow_html=True)
    
    if st.session_state.files:
        selected_file = st.selectbox("📁 Chọn file để kiểm duyệt:", list(st.session_state.files.keys()))
        if selected_file:
            edited_code = st.text_area(
                f"📝 Chỉnh sửa file code '{selected_file}':",
                value=st.session_state.files[selected_file],
                height=350
            )
            st.session_state.files[selected_file] = edited_code
    else:
        st.warning("Không tìm thấy file mã nguồn nào để chỉnh sửa.")
        
    code_feedback = st.text_input(
        "🔄 Ý kiến đóng góp / Yêu cầu code lại (nếu có):", 
        placeholder="Ví dụ: Chuyển sang sử dụng pandas thay vì numpy..."
    )
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Đồng ý code & Tiến hành kiểm thử QA 🛡️", use_container_width=True):
            reconstructed = ""
            for filepath, content in st.session_state.files.items():
                reconstructed += f"### FILE: {filepath}\n```python\n{content}\n```\n\n"
            st.session_state.raw_code = reconstructed
            st.session_state.pipeline_step = "run_qa"
            st.rerun()
            
    with col2:
        if st.button("Lập trình lại dựa trên feedback 🔄", use_container_width=True):
            if not code_feedback.strip():
                st.warning("Vui lòng điền ý kiến đóng góp trước khi yêu cầu viết lại.")
            else:
                try:
                    orchestrator = get_orchestrator()
                    reconstructed = ""
                    for filepath, content in st.session_state.files.items():
                        reconstructed += f"### FILE: {filepath}\n```python\n{content}\n```\n\n"
                        
                    with st.spinner("💻 Senior Developer đang lập trình lại..."):
                        new_raw_code = orchestrator.run_developer(
                            design_doc=st.session_state.design_doc,
                            user_requirement=st.session_state.user_requirement,
                            feedback=code_feedback,
                            previous_code=reconstructed,
                            search_context=st.session_state.search_context
                        )
                        st.session_state.raw_code = new_raw_code
                        st.session_state.files = orchestrator._parse_files_with_fallback(new_raw_code)
                        st.success("Đã hoàn thành viết lại code!")
                        time.sleep(1)
                        st.rerun()
                except Exception as e:
                    st.error(f"Lỗi khi lập trình lại: {e}")

# Transition step: Run QA Loop
elif st.session_state.pipeline_step == "run_qa":
    st.info("🛡️ Đang chạy vòng thử nghiệm và sửa lỗi tự động...")
    try:
        orchestrator = get_orchestrator()
        context = orchestrator.run_qa_loop(
            design_doc=st.session_state.design_doc,
            raw_code_input=st.session_state.raw_code,
            user_requirement=st.session_state.user_requirement,
            status_callback=update_qa_status,
            search_context=st.session_state.search_context
        )
        st.session_state.files = context.files
        st.session_state.final_review = context.final_review
        st.session_state.execution_history = context.execution_history
        st.session_state.zip_data = context.zip_data
        st.session_state.pipeline_step = "completed"
        st.rerun()
    except Exception as e:
        st.error(f"Lỗi khi kiểm thử QA: {e}")
        if st.button("Quay lại"):
            st.session_state.pipeline_step = "review_code"
            st.rerun()

# Step 3: PIPELINE COMPLETED
elif st.session_state.pipeline_step == "completed":
    st.success("🎉 Toàn bộ pipeline đã hoàn tất thành công!")
    
    tab_code, tab_report, tab_design, tab_history = st.tabs([
        "💻 Workspace Files (Mã nguồn dự án)", 
        "🛡️ QA Review Report & Raw Output", 
        "📐 Design Document (Architect)",
        "📊 Run History"
    ])
    
    with tab_code:
        if st.session_state.files:
            selected_file = st.selectbox("📁 Chọn file để xem nội dung:", list(st.session_state.files.keys()))
            if selected_file:
                st.code(st.session_state.files[selected_file])
                
            st.markdown("---")
            
            if st.session_state.zip_data:
                st.download_button(
                    label="📥 Tải về trọn bộ dự án (.zip)",
                    data=st.session_state.zip_data,
                    file_name="workspace_project.zip",
                    mime="application/zip",
                    use_container_width=True
                )
        else:
            st.warning("Không tìm thấy mã nguồn nào được tạo ra.")
            
    with tab_report:
        st.markdown(st.session_state.final_review)
        
    with tab_design:
        st.markdown(st.session_state.design_doc)
        
    with tab_history:
        st.markdown("### 📊 Lịch sử các vòng biên dịch/chạy thử code")
        if st.session_state.execution_history:
            for run in st.session_state.execution_history:
                status_text = "🟢 THÀNH CÔNG" if run["success"] else "🔴 THẤT BẠI"
                with st.expander(f"Vòng {run['iteration']}: {status_text} (Exit Code: {run['exit_code']})"):
                    if run["stderr"]:
                        st.markdown("**Lỗi (Stderr):**")
                        st.code(run["stderr"])
                    if run["stdout"]:
                        st.markdown("**Đầu ra (Stdout):**")
                        st.code(run["stdout"])
        else:
            st.info("Không tìm thấy dữ liệu lịch sử chạy thử nghiệm.")
            
    st.markdown("---")
    if st.button("🆕 Bắt đầu dự án mới", use_container_width=True):
        st.session_state.pipeline_step = "idle"
        st.session_state.user_requirement = ""
        st.session_state.design_doc = ""
        st.session_state.raw_code = ""
        st.session_state.files = {}
        st.session_state.final_review = ""
        st.session_state.zip_data = None
        st.session_state.execution_history = []
        st.session_state.search_context = ""
        st.rerun()
