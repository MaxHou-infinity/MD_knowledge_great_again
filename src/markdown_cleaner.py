import os
import time
from pathlib import Path
from typing import List, Tuple, Dict, Any, Optional
from openai import OpenAI

from config import (
    DEEPSEEK_API_KEY,
    DEEPSEEK_API_ENDPOINT,
    DEEPSEEK_MODEL,
    MAX_RETRIES,
    TIMEOUT,
    CLEANED_FILE_PREFIX
)

class MarkdownCleaner:
    """使用Deepseek API清洗Markdown文件的处理器"""
    
    def __init__(self, api_key: Optional[str] = None, api_endpoint: Optional[str] = None, model: Optional[str] = None):
        """初始化清洗处理器
        
        Args:
            api_key: Deepseek API密钥，如果为None则使用配置文件中的密钥
            api_endpoint: API端点，如果为None则使用配置文件中的端点
            model: 模型名称，如果为None则使用配置文件中的模型
        """
        self.api_key = api_key or DEEPSEEK_API_KEY
        self.api_endpoint = api_endpoint or DEEPSEEK_API_ENDPOINT
        self.model = model or DEEPSEEK_MODEL
        
        # 验证必要参数
        if not self.api_key:
            raise ValueError("API密钥不能为空")
        
        # 初始化OpenAI客户端
        try:
            self.client = OpenAI(
                api_key=self.api_key,
                base_url=self.api_endpoint,
                timeout=TIMEOUT  # 设置全局超时
            )
        except Exception as e:
            raise Exception(f"初始化OpenAI客户端失败: {str(e)}")
        
    def _call_api(self, content: str, callback=None) -> str:
        """调用Deepseek API清洗Markdown内容
        
        Args:
            content: 原始Markdown内容
            callback: 回调函数用于报告进度
            
        Returns:
            清洗后的Markdown内容
            
        Raises:
            Exception: API调用失败
        """
        system_message = """你是一个专业的Markdown文档清洗专家。你的任务是清洗网页抓取的Markdown文件，使其更适合向量模型分析和存储。
请遵循以下清洗原则：
1. 删除无用的页面标题、菜单信息、页脚信息、广告等干扰内容
2. 完整保留文档中的重要观点、核心文本、代码块、索引、网址和图片链接
3. 可以对语义进行适当重组和简化，但必须保持原意精准
4. 保持Markdown格式的完整性和一致性
5. 返回的内容必须是完整的Markdown文本，不要添加任何评论或解释"""

        user_message = f"请清洗以下Markdown文档，使其更适合向量分析:\n\n{content}"
        
        # 截断过长内容以防止API限制
        max_content_length = 100000  # 约10万字符
        if len(user_message) > max_content_length:
            if callback:
                callback("内容截断", 15, f"文档过长，已截断到前{max_content_length}字符")
            user_message = user_message[:max_content_length] + "\n\n[内容已截断，仅处理前部分]"
        
        # 重试机制
        for attempt in range(MAX_RETRIES):
            try:
                if callback:
                    callback("API调用", 25 + (attempt * 5), f"正在调用API (尝试 {attempt+1}/{MAX_RETRIES})...")
                
                # 使用OpenAI库1.68.2版本的API调用方式
                start_time = time.time()
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_message},
                        {"role": "user", "content": user_message}
                    ],
                    timeout=TIMEOUT,
                    max_tokens=4000  # 限制返回的令牌数量
                )
                elapsed_time = time.time() - start_time
                
                if callback:
                    callback("API调用", 40, f"API响应成功，用时 {elapsed_time:.2f} 秒")
                
                # 确保我们能够正确访问响应内容
                if hasattr(response, 'choices') and len(response.choices) > 0 and hasattr(response.choices[0], 'message'):
                    return response.choices[0].message.content
                else:
                    raise Exception("API响应格式不正确")
                
            except Exception as e:
                error_msg = str(e)
                
                # 特殊处理超时错误
                if "timeout" in error_msg.lower() or "timed out" in error_msg.lower():
                    if callback:
                        callback("API调用", -1, f"API请求超时 (尝试 {attempt+1}/{MAX_RETRIES}): 服务器响应时间过长")
                    if attempt == MAX_RETRIES - 1:
                        raise Exception(f"API请求超时，服务器响应时间过长。请稍后再试或减小文件大小。")
                
                # 特殊处理模型不存在的错误
                elif "Model Not Exist" in error_msg or "invalid_request_error" in error_msg:
                    raise Exception(f"模型'{self.model}'不存在，请检查模型名称是否正确。可用模型: deepseek-chat, deepseek-coder")
                
                # 特殊处理API密钥错误
                elif "authentication" in error_msg.lower() or "api key" in error_msg.lower() or "unauthorized" in error_msg.lower():
                    raise Exception(f"API认证失败: API密钥无效或已过期")
                
                # 其他错误
                elif attempt == MAX_RETRIES - 1:
                    raise Exception(f"API调用失败 (尝试 {attempt+1}/{MAX_RETRIES}): {error_msg}")
                
                if callback:
                    callback("API调用", 25, f"API调用失败 (尝试 {attempt+1}/{MAX_RETRIES}): 准备重试...")
                
                # 指数退避
                wait_time = 2 ** attempt
                if callback:
                    callback("API调用", 25, f"等待 {wait_time} 秒后重试...")
                
                time.sleep(wait_time)
                
        raise Exception("API调用失败，已达到最大重试次数")
    
    def clean_file(self, file_path: str, callback=None) -> Tuple[bool, str]:
        """清洗单个Markdown文件
        
        Args:
            file_path: Markdown文件路径
            callback: 进度回调函数，接收(file_path, progress, message)参数
            
        Returns:
            (成功标志, 输出文件路径或错误信息)
        """
        try:
            if callback:
                callback(file_path, 0, "开始处理文件")
                
            # 检查文件是否存在
            if not os.path.exists(file_path):
                return False, f"文件不存在: {file_path}"
                
            # 检查文件扩展名
            if not file_path.lower().endswith(('.md', '.markdown')):
                return False, f"不支持的文件类型: {file_path}"
            
            # 获取文件大小
            file_size = os.path.getsize(file_path) / 1024  # KB
            if callback:
                callback(file_path, 5, f"文件大小: {file_size:.2f} KB")
                
            # 读取文件内容
            try:
                if callback:
                    callback(file_path, 10, "正在读取文件内容...")
                
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                if callback:
                    callback(file_path, 20, f"文件读取完成，共 {len(content)} 字符")
            except UnicodeDecodeError:
                # 尝试使用其他编码
                if callback:
                    callback(file_path, 10, "UTF-8编码失败，尝试GBK编码...")
                    
                try:
                    with open(file_path, 'r', encoding='gbk') as f:
                        content = f.read()
                    if callback:
                        callback(file_path, 20, f"文件读取完成(GBK编码)，共 {len(content)} 字符")
                except Exception as enc_error:
                    return False, f"无法读取文件，编码问题: {str(enc_error)}"
                
            # 调用API清洗内容
            if callback:
                callback(file_path, 25, "准备调用API处理内容...")
                
            cleaned_content = self._call_api(content, lambda phase, progress, msg: 
                callback(file_path, progress, msg) if callback else None)
            
            if callback:
                callback(file_path, 60, "API处理完成，准备保存文件")
                
            # 生成输出文件路径
            file_dir = os.path.dirname(file_path)
            file_name = os.path.basename(file_path)
            base_name, ext = os.path.splitext(file_name)
            output_file = os.path.join(file_dir, f"{CLEANED_FILE_PREFIX}{base_name}{ext}")
            
            # 保存清洗后的内容
            try:
                if callback:
                    callback(file_path, 80, "正在保存清洗后的内容...")
                
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(cleaned_content)
                    
                if callback:
                    callback(file_path, 100, f"处理完成，已保存至 {output_file}")
            except Exception as save_error:
                return False, f"保存文件失败: {str(save_error)}"
                
            return True, output_file
        except Exception as e:
            if callback:
                callback(file_path, -1, f"处理失败: {str(e)}")
            return False, str(e)
    
    def clean_directory(self, dir_path: str, callback=None) -> List[Tuple[str, bool, str]]:
        """清洗目录中的所有Markdown文件
        
        Args:
            dir_path: 目录路径
            callback: 进度回调函数，接收(file_path, progress, message)参数
            
        Returns:
            处理结果列表，每项为(文件路径, 成功标志, 输出文件路径或错误信息)
        """
        results = []
        
        # 检查目录是否存在
        if not os.path.isdir(dir_path):
            if callback:
                callback(dir_path, -1, f"目录不存在: {dir_path}")
            return [(dir_path, False, f"目录不存在: {dir_path}")]
        
        # 获取所有Markdown文件
        md_files = []
        for root, _, files in os.walk(dir_path):
            for file in files:
                if file.lower().endswith(('.md', '.markdown')):
                    md_files.append(os.path.join(root, file))
        
        if not md_files:
            if callback:
                callback(dir_path, 100, "目录中没有找到Markdown文件")
            return [(dir_path, True, "目录中没有找到Markdown文件")]
        
        # 处理每个文件
        total_files = len(md_files)
        if callback:
            callback(dir_path, 0, f"找到 {total_files} 个Markdown文件")
            
        for i, file_path in enumerate(md_files):
            if callback:
                overall_progress = int((i / total_files) * 100)
                callback(dir_path, overall_progress, f"正在处理 ({i+1}/{total_files}): {os.path.basename(file_path)}")
            
            success, result = self.clean_file(file_path, callback)
            results.append((file_path, success, result))
        
        if callback:
            callback(dir_path, 100, f"所有文件处理完成，共 {total_files} 个文件")
        
        return results 