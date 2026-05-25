import streamlit as st
import re
import os
import time
from llm import LLMClient
from agents import ArchitectAgent, DeveloperAgent, QAAgent
from orchestrator import Orchestrator

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
    .agent-card {
        padding: 1.5rem;
        border-radius: 10px;
        background-color: #F8F9FA;
        border-left: 5px solid #6C63FF;
        margin-bottom: 1rem;
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
</style>
""", unsafe_allow_html=True)

# Helper function to extract code and extension from Markdown output
def extract_code_and_ext(text):
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
            "html": ".html", "css": ".css",
            "cpp": ".cpp", "c": ".c",
            "java": ".java", "rust": ".rs", "rs": ".rs",
            "go": ".go", "bash": ".sh", "sh": ".sh",
            "sql": ".sql", "json": ".json", "xml": ".xml"
        }
        ext = ext_map.get(lang.lower(), ".txt")
        return code.strip(), ext
    return "", ".txt"

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

# Helper function to get model selection elements
def configure_agent_model(agent_label, prefix_id):
    st.sidebar.subheader(agent_label)
    
    # 1. Select provider
    provider = st.sidebar.selectbox(
        f"Nhà cung cấp [{prefix_id}]",
        ["Gemini", "Groq", "OpenAI", "Anthropic", "Custom"],
        key=f"provider_{prefix_id}"
    )
    
    # Define models list for each provider
    models_dict = {
        "Gemini": ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-2.0-flash-exp", "gemini-1.0-pro", "Custom Model..."],
        "Groq": ["llama-3.3-70b-versatile", "llama-3.1-70b-versatile", "llama3-70b-8192", "llama3-8b-8192", "mixtral-8x7b-32768", "gemma2-9b-it", "Custom Model..."],
        "OpenAI": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-4", "gpt-3.5-turbo", "o1-mini", "o1-preview", "Custom Model..."],
        "Anthropic": ["claude-3-5-sonnet-latest", "claude-3-5-haiku-latest", "claude-3-opus-latest", "claude-3-sonnet-20240229", "claude-3-haiku-20240307", "Custom Model..."],
        "Custom": ["Custom Model..."]
    }
    
    # 2. Select model option
    model_option = st.sidebar.selectbox(
        f"Mô hình [{prefix_id}]",
        models_dict[provider],
        key=f"model_opt_{prefix_id}"
    )
    
    # 3. Handle custom model name input
    if model_option == "Custom Model...":
        model_name = st.sidebar.text_input(
            f"Điền tên Model tùy chỉnh [{prefix_id}]",
            value="",
            placeholder="Ví dụ: gpt-4-32k hoặc qwen-2.5-coder",
            key=f"custom_name_{prefix_id}"
        )
    else:
        model_name = model_option
        
    # 4. Temperature configuration
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

# Configure 3 agents
arch_provider, arch_model, arch_temp = configure_agent_model("📐 Agent 1: System Architect", "1")
st.sidebar.markdown("---")
dev_provider, dev_model, dev_temp = configure_agent_model("💻 Agent 2: Senior Developer", "2")
st.sidebar.markdown("---")
qa_provider, qa_model, qa_temp = configure_agent_model("🛡️ Agent 3: QA Engineer", "3")


# --- MAIN INTERFACE ---
st.markdown("<h1 class='main-header'>🤖 Multi-Agent Auto-Coding Lab</h1>", unsafe_allow_html=True)
st.markdown("<p class='sub-header'>Hệ thống Đa Tác tử Phối hợp Tự động Lập trình (System Architect → Senior Developer → QA Engineer)</p>", unsafe_allow_html=True)

# User Requirements input
st.subheader("💡 Nhập yêu cầu phát triển phần mềm")
user_requirement = st.text_area(
    "Mô tả chi tiết những gì bạn muốn hệ thống lập trình:",
    height=150,
    placeholder="Ví dụ: Viết một hàm Python tải một file từ URL và hiển thị thanh tiến trình download..."
)

st.markdown("### ⚡ Tiến trình hoạt động của các Agent")

# Status and log placeholders
architect_box = st.empty()
developer_box = st.empty()
qa_box = st.empty()

# Custom callback function to handle real-time pipeline status updates
def update_status(event_type, message, data=None):
    if event_type == "architect_start":
        st.session_state.arch_status = architect_box.status(message, expanded=True)
    elif event_type == "architect_end":
        st.session_state.arch_status.update(label="✅ " + message, state="complete", expanded=False)
        with st.session_state.arch_status:
            st.markdown(data)
    elif event_type == "architect_error":
        st.session_state.arch_status.update(label=message, state="error", expanded=True)
        
    elif event_type == "developer_start":
        st.session_state.dev_status = developer_box.status(message, expanded=True)
    elif event_type == "developer_end":
        st.session_state.dev_status.update(label="✅ " + message, state="complete", expanded=False)
        with st.session_state.dev_status:
            st.code(data)
    elif event_type == "developer_error":
        st.session_state.dev_status.update(label=message, state="error", expanded=True)
        
    elif event_type == "qa_start":
        st.session_state.qa_status = qa_box.status(message, expanded=True)
    elif event_type == "qa_end":
        st.session_state.qa_status.update(label="✅ " + message, state="complete", expanded=True)
        with st.session_state.qa_status:
            st.markdown(data)
    elif event_type == "qa_error":
        st.session_state.qa_status.update(label=message, state="error", expanded=True)

# Submit action
if st.button("🚀 Khởi chạy hệ thống tác tử", use_container_width=True):
    # Validations
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
        
    # Check custom model names are filled
    missing_model_names = []
    if arch_model == "" or (arch_model == "Custom Model..." and not st.session_state.get("custom_name_1", "").strip()):
        missing_model_names.append("System Architect")
    if dev_model == "" or (dev_model == "Custom Model..." and not st.session_state.get("custom_name_2", "").strip()):
        missing_model_names.append("Senior Developer")
    if qa_model == "" or (qa_model == "Custom Model..." and not st.session_state.get("custom_name_3", "").strip()):
        missing_model_names.append("QA Engineer")
        
    if not user_requirement.strip():
        st.error("Vui lòng nhập yêu cầu của bạn trước khi chạy.")
    elif missing_keys:
        st.error(f"❌ Thiếu khóa API/Cấu hình của các nhà cung cấp được lựa chọn: {', '.join(missing_keys)}")
    elif missing_model_names:
        st.error(f"❌ Vui lòng nhập tên Model tùy chỉnh cho các Agent: {', '.join(missing_model_names)}")
    else:
        # Pre-clear visual boxes
        architect_box.empty()
        developer_box.empty()
        qa_box.empty()
        
        # Initialize LLM Client
        try:
            # Resolve actual model names if they were custom
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
            
            # Initialize Agents
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
            
            # Initialize Orchestrator
            orchestrator = Orchestrator(architect, developer, qa)
            
            # Run pipeline
            start_time = time.time()
            context = orchestrator.run_pipeline(
                user_requirement=user_requirement,
                status_callback=update_status
            )
            elapsed_time = time.time() - start_time
            
            # Show completed summary
            st.success(f"🎉 Toàn bộ pipeline đã hoàn tất thành công trong {elapsed_time:.1f} giây!")
            
            # Extract final code
            final_code, file_ext = extract_code_and_ext(context.final_review)
            
            # Layout for results tabs
            st.markdown("### 🏆 Kết quả đầu ra")
            tab_code, tab_report, tab_design = st.tabs([
                "💻 Final Optimized Code", 
                "🛡️ QA Review Report & Raw Output", 
                "📐 Design Document (Architect)"
            ])
            
            with tab_code:
                if final_code:
                    st.code(final_code)
                    
                    # Add download button
                    file_name = f"final_output{file_ext}"
                    st.download_button(
                        label="📥 Tải mã nguồn về máy",
                        data=final_code,
                        file_name=file_name,
                        mime="text/plain",
                        use_container_width=True
                    )
                else:
                    st.warning("Không tìm thấy khối mã nguồn độc lập trong kết quả của QA. Bạn có thể xem mã nguồn trong báo cáo chi tiết ở tab bên cạnh.")
                    
            with tab_report:
                st.markdown(context.final_review)
                
            with tab_design:
                st.markdown(context.design_doc)
                
        except Exception as e:
            st.error(f"❌ Đã xảy ra lỗi hệ thống trong quá trình thực thi: {str(e)}")
            st.info("💡 Vui lòng kiểm tra lại API Key, kết nối mạng và tên mô hình.")
