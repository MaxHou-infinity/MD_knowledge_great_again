import streamlit as st
from web_crawler import WebCrawler
import os
import glob
from markdown_cleaner import MarkdownCleaner
from config import DEEPSEEK_API_KEY, DEEPSEEK_API_ENDPOINT, DEEPSEEK_MODEL

# 设置页面标题
st.set_page_config(page_title="网页爬虫与Markdown清洗工具", layout="wide")

# 创建标签页
tab1, tab2 = st.tabs(["网页爬虫", "Markdown清洗"])

# 标签页1: 网页爬虫
with tab1:
    st.title('网页爬虫工具')

    # 输入区域
    url = st.text_input('请输入起始URL', 'https://example.com', key='crawler_url')

    # 设置默认保存路径
    default_save_path = './output'

    # 使用文本输入显示当前保存路径
    save_path = st.text_input('保存路径', value=default_save_path, key='crawler_save_path')

    # 添加文件夹选择按钮
    if st.button('选择其他保存文件夹', key='crawler_select_folder'):
        st.session_state['show_folder_input'] = True

    # 显示文件夹选择输入框
    if 'show_folder_input' in st.session_state and st.session_state['show_folder_input']:
        new_path = st.text_input('请输入新的保存路径', key='crawler_new_path')
        if st.button('确认路径', key='crawler_confirm_path'):
            save_path = new_path
            st.session_state['save_path'] = new_path
            st.session_state['show_folder_input'] = False
            st.success(f'已更新保存路径: {new_path}')

    # 如果之前已选择路径，则使用已选择的路径
    if 'save_path' in st.session_state:
        save_path = st.session_state['save_path']

    if st.button('开始爬取', key='crawler_start'):
        if url and save_path:
            try:
                # 显示进度信息
                progress_text = st.empty()
                progress_text.text('正在初始化爬虫...')
                
                # 创建爬虫实例并开始爬取
                crawler = WebCrawler()
                
                # 更新状态
                progress_text.text('开始爬取网页...')
                crawler.crawl(url, save_path)
                
                # 完成提示
                st.success(f'爬取完成！文件已保存到: {os.path.abspath(save_path)}')
                
            except Exception as e:
                st.error(f'发生错误: {str(e)}')
        else:
            st.warning('请输入URL和保存路径')

# 标签页2: Markdown清洗
with tab2:
    st.title('Markdown清洗工具')
    
    # API设置区域
    st.subheader('API设置')
    
    # 显示API使用帮助信息
    with st.expander("DeepSeek API 使用说明", expanded=False):
        st.markdown("""
        ## 如何配置 DeepSeek API
        
        1. 获取 [DeepSeek](https://platform.deepseek.com/api_keys) 的 API 密钥
        2. 填写以下配置信息：
           - API Key: 你的 DeepSeek API 密钥
           - API 端点已设置为默认值: `https://api.deepseek.com`
           - 模型名称已设置为默认值: `deepseek-chat` (DeepSeek-V3模型)
           
        ### 常见问题：
        
        1. **如遇到"Model Not Exist"错误**：
           - 确认使用的模型名称正确。DeepSeek支持的模型有：
             - `deepseek-chat`: 通用对话模型（V3版本）
             - `deepseek-coder`: 代码专用模型
             - `deepseek-reasoner`: 推理专用模型(R1)
           
        2. **如遇到API调用失败**：
           - 检查API密钥是否正确
           - 确认网络连接正常
           - 检查API调用次数限制
           
        3. **如遇到超时问题**：
           - 大型文件处理可能需要较长时间
           - 可适当减小文件大小或拆分文件
           - 当前超时设置为120秒
        """)
    
    col1, col2 = st.columns(2)
    with col1:
        api_key = st.text_input('DeepSeek API Key', value=DEEPSEEK_API_KEY, type='password', help='输入你的DeepSeek API密钥')
    
    with col2:
        api_endpoint = st.text_input('API端点', value=DEEPSEEK_API_ENDPOINT, help='API请求地址，通常不需要修改')
    
    model = st.text_input('模型名称', value=DEEPSEEK_MODEL, help='使用的模型名称，通常不需要修改')
    
    # 分隔线
    st.markdown('---')
    
    # 文件选择区域
    st.subheader('选择要处理的文件或目录')
    
    option = st.radio('处理模式', ['单个文件', '整个目录'])
    
    if option == '单个文件':
        file_path = st.text_input('Markdown文件路径', help='输入.md或.markdown文件的完整路径')
        
        if st.button('浏览文件', key='md_browse_file'):
            st.info('请直接在上方输入框中输入文件路径')
    else:
        dir_path = st.text_input('目录路径', help='输入包含Markdown文件的目录路径')
        
        if st.button('浏览目录', key='md_browse_dir'):
            st.info('请直接在上方输入框中输入目录路径')
    
    # 高级选项
    with st.expander("高级选项", expanded=False):
        max_tokens = st.slider("最大输出令牌数", min_value=1000, max_value=8000, value=4000, step=500, 
                              help="控制输出文本的最大长度")
        timeout_value = st.slider("API超时时间(秒)", min_value=30, max_value=300, value=120, step=30,
                                 help="API请求的最大等待时间")
    
    # 处理按钮
    if st.button('开始清洗', key='md_start_clean'):
        # 检查API密钥
        if not api_key:
            st.error('请设置有效的DeepSeek API密钥')
        else:
            # 初始化进度信息
            progress_container = st.container()
            with progress_container:
                progress_bar = st.progress(0)
                status_text = st.empty()
                detailed_text = st.empty()
                results_area = st.container()
            
            # 创建清洗器实例
            try:
                cleaner = MarkdownCleaner(api_key=api_key, api_endpoint=api_endpoint, model=model)
                
                # 处理回调函数
                def update_progress(path, progress, message):
                    # 更新进度条
                    if progress >= 0:
                        progress_bar.progress(progress / 100)
                    
                    # 更新状态文本
                    file_name = os.path.basename(path) if os.path.exists(path) else path
                    status_text.text(f"处理: {file_name} - {progress}%")
                    detailed_text.text(message)
                    
                    # 如果是文件完成或失败，添加到结果区域
                    if progress == 100 or progress == -1:
                        with results_area:
                            if progress == 100:
                                st.success(f"{file_name}: {message}")
                            else:
                                st.error(f"{file_name}: {message}")
                
                try:
                    if option == '单个文件':
                        # 检查路径
                        if not file_path:
                            st.error('请输入文件路径')
                        elif not os.path.exists(file_path):
                            st.error(f'文件不存在: {file_path}')
                        else:
                            status_text.text('开始处理文件...')
                            
                            # 配置显示实时状态
                            status_container = st.empty()
                            status_container.info("正在处理中，请耐心等待...")
                            
                            # 开始处理
                            success, result = cleaner.clean_file(file_path, update_progress)
                            
                            # 更新最终状态
                            if success:
                                progress_bar.progress(100)
                                status_container.success(f'处理完成！清洗后的文件已保存到: {result}')
                            else:
                                progress_bar.progress(0)
                                status_container.error(f'处理失败: {result}')
                    else:
                        # 检查路径
                        if not dir_path:
                            st.error('请输入目录路径')
                        elif not os.path.isdir(dir_path):
                            st.error(f'目录不存在: {dir_path}')
                        else:
                            status_text.text('开始处理目录...')
                            
                            # 配置显示实时状态
                            status_container = st.empty()
                            status_container.info("正在处理中，请耐心等待...")
                            
                            # 开始处理
                            results = cleaner.clean_directory(dir_path, update_progress)
                            
                            # 汇总结果
                            total = len(results)
                            success_count = sum(1 for _, success, _ in results if success)
                            
                            # 更新最终状态
                            progress_bar.progress(100)
                            status_container.success(f'全部处理完成！共 {total} 个文件，成功 {success_count} 个，失败 {total - success_count} 个')
                            
                            # 显示每个文件的处理结果
                            if total > 0:
                                st.subheader('处理结果明细')
                                for file_path, success, result in results:
                                    if success:
                                        st.markdown(f'✅ **{os.path.basename(file_path)}**: 已保存到 `{result}`')
                                    else:
                                        st.markdown(f'❌ **{os.path.basename(file_path)}**: {result}')
                except Exception as e:
                    error_message = str(e)
                    if "timeout" in error_message.lower():
                        st.error(f'处理超时: {error_message}\n\n可能原因：文件过大或API响应慢。尝试减小文件大小或稍后再试。')
                    elif "api key" in error_message.lower() or "unauthorized" in error_message.lower():
                        st.error(f'API密钥错误: {error_message}\n\n请检查您的API密钥是否正确。')
                    else:
                        st.error(f'处理过程中发生错误: {error_message}')
                    progress_bar.progress(0)
            except Exception as e:
                st.error(f'初始化API客户端失败: {str(e)}')
                st.info("解决建议: 请确保API密钥正确且有效，API端点可访问，并且网络连接正常。")
                progress_bar.progress(0)