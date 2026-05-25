import logging
import requests
from duckduckgo_search import DDGS

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("MultiAgentAutoCodingLab.Search")

def search_tavily(query, api_key, max_results=3):
    """
    Searches Tavily API for the given query and returns formatted snippets.
    """
    try:
        url = "https://api.tavily.com/search"
        payload = {
            "api_key": api_key,
            "query": query,
            "max_results": max_results,
            "search_depth": "basic",
            "include_answer": False
        }
        response = requests.post(url, json=payload, timeout=15)
        response.raise_for_status()
        data = response.json()
        results = data.get("results", [])
        if not results:
            return f"Tavily: Không tìm thấy kết quả nào cho truy vấn: '{query}'"
            
        formatted = []
        for r in results:
            title = r.get("title", "No Title")
            href = r.get("url", "#")
            body = r.get("content", "No Description")
            formatted.append(f"Tiêu đề: {title}\nLiên kết: {href}\nTóm tắt: {body}\n")
        return "\n---\n".join(formatted)
    except Exception as e:
        logger.error(f"Error during Tavily search: {e}")
        return f"Lỗi tìm kiếm Tavily: {str(e)}"

def search_web(query, max_results=3, tavily_api_key=None):
    """
    Searches DuckDuckGo or Tavily for the given query and returns formatted snippets.
    """
    if tavily_api_key and tavily_api_key.strip():
        logger.info(f"Using Tavily for query: '{query}'")
        return search_tavily(query, tavily_api_key.strip(), max_results=max_results)

    logger.info(f"Using DuckDuckGo for query: '{query}'")
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
            if not results:
                return (
                    f"Không tìm thấy kết quả nào cho truy vấn: '{query}'.\n"
                    "Lưu ý: Có thể DuckDuckGo đang yêu cầu xác minh Captcha hoặc chặn IP từ máy chủ của bạn. "
                    "Hãy điền 'Tavily Search API Key' trong sidebar để tìm kiếm ổn định và chính xác hơn."
                )
                
            formatted = []
            for r in results:
                title = r.get("title", "No Title")
                href = r.get("href", "#")
                body = r.get("body", "No Description")
                formatted.append(f"Tiêu đề: {title}\nLiên kết: {href}\nTóm tắt: {body}\n")
            return "\n---\n".join(formatted)
    except Exception as e:
        logger.error(f"Error during DuckDuckGo search: {e}")
        return (
            f"Lỗi tìm kiếm DuckDuckGo: {str(e)}.\n"
            "Hãy điền 'Tavily Search API Key' trong sidebar để tìm kiếm ổn định và chính xác hơn."
        )

def generate_search_context(llm_client, user_requirement, provider, model_name, tavily_api_key=None, status_callback=None):
    """
    Generates search queries based on user requirements, runs web searches,
    and returns a consolidated Markdown documentation context.
    """
    system_prompt = (
        "Bạn là một Assistant phân tích thông tin. Dựa trên yêu cầu phần mềm của khách hàng, "
        "hãy tạo ra tối đa 2 câu lệnh tìm kiếm Google (ưu tiên bằng Tiếng Anh để có kết quả tốt nhất) "
        "nhằm tra cứu tài liệu hướng dẫn (API Documentation) hoặc ví dụ sử dụng của các thư viện liên quan.\n"
        "QUY TẮC BẮT BUỘC:\n"
        "1. Mỗi câu lệnh tìm kiếm trên một dòng.\n"
        "2. Chỉ trả về các dòng câu lệnh tìm kiếm, KHÔNG giải thích, KHÔNG thêm số thứ tự, KHÔNG để trong code block."
    )
    
    try:
        if status_callback:
            status_callback("search_queries_start", "🔍 Đang tạo truy vấn tìm kiếm tài liệu thư viện...", None)
            
        response_text = llm_client.call_model(
            provider=provider,
            model_name=model_name,
            system_prompt=system_prompt,
            prompt=user_requirement,
            temperature=0.3
        )
        
        # Parse queries
        queries = [q.strip() for q in response_text.strip().split("\n") if q.strip()]
        # Filter out markdown formatting if any was generated
        queries = [q.replace("`", "").replace("*", "").replace("-", "").strip() for q in queries]
        queries = [q for q in queries if q]
        queries = queries[:2]  # Limit to 2 queries to be fast
        
        if not queries:
            if status_callback:
                status_callback("search_queries_end", "🔍 Bỏ qua tra cứu tài liệu (Không đề xuất truy vấn).", None)
            return ""
            
        search_contexts = []
        for q in queries:
            if status_callback:
                status_callback("search_exec_start", f"🔍 Đang tra cứu tài liệu trực tuyến cho: '{q}'...", None)
                
            results_text = search_web(q, tavily_api_key=tavily_api_key)
            search_contexts.append(f"### Tài liệu tra cứu cho: '{q}'\n\n{results_text}")
            
        consolidated = "\n\n==================================================\n\n".join(search_contexts)
        
        if status_callback:
            status_callback("search_queries_end", "🔍 Đã hoàn thành tra cứu tài liệu thư viện.", consolidated)
            
        return consolidated
        
    except Exception as e:
        logger.error(f"Error generating search context: {e}")
        if status_callback:
            status_callback("search_error", f"⚠️ Lỗi tra cứu tài liệu trực tuyến: {str(e)}", None)
        return f"⚠️ Lỗi tra cứu tài liệu trực tuyến: {str(e)}"
