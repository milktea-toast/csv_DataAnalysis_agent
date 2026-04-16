import os
from langchain_experimental.agents.agent_toolkits import create_pandas_dataframe_agent
from langchain_community.llms import Tongyi # LangChain对接Qwen大模型 的官方工具类。让你的 Python 代码能调用通义千问 AI（如 qwen-turbo、qwen-plus 等）

def dataframe_agent(api_key, df, query):
    # 初始化通义千问大模型
    llm = Tongyi( #使用Tongyi,不需要手动设置base_url
        model_name="qwen-plus",
        api_key=os.getenv("DASHSCOPE_API_KEY"), # 从环境变量读取 API Key 给变量
        temperature=0,  # 数据分析必须设为 0，保证准确
        max_tokens=2048
    )

    # 3. 创建 Pandas 数据分析智能体（关键配置：格式化输出）
    agent = create_pandas_dataframe_agent(
        llm=llm,
        df=df,
        agent_type="zero-shot-react-description",
        agent_executor_kwargs={"handle_parsing_errors": True},# 智能体输出格式乱了、少了 Action、格式不对时，不崩溃、不报错、自动跳过错误，直接返回答案
        verbose=True,# 打印完整思考过程
    )

    try: # 小心尝试
        # 4. 调用智能体
        response=agent.invoke({"input": query})

        # 5. 直接返回结果（不再强行解析 JSON）
        return response # 成功就返回答案

    except Exception as e:
        return f"数据分析出错：{str(e)}" # 失败就返回错误，不崩溃

"""
测试
import os
import json
import pandas as pd
df = pd.read_csv("personal_data.csv")

print(dataframe_agent(os.getenv("DASHSCOPE_API_KEY"), df, "数据里出现最多的职业是什么?")) #直接调用了环境变量里储存的API密钥，或者修改为前面写入api 密钥，方便后面网页

"""

# 不包含prompt 和 PROMPT_TEMPLATE