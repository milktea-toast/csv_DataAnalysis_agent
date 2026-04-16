import pandas as pd
import json
import streamlit as st # 用于制作网页,并有现成的函数展示DataFrame等
from utilsfinal import dataframe_agent

# 新增：可视化类型映射（简化指令解析）
VISUAL_TYPES = {
    "散点图": st.scatter_chart,
    "折线图": st.line_chart,
    "条形图": st.bar_chart,
    "柱状图": st.bar_chart  # 兼容不同表述
}


st.title("💡 CSV数据分析智能工具") # 给网页加一个标题
with st.sidebar: # 给网页添加侧边栏组件
    api_key = st.text_input("请输入API密钥：", type="password")
    st.markdown("[获取API key](https://bailian.console.aliyun.com/cn-beijing#/home)")

data = st.file_uploader("上传你的数据文件（CSV格式）：", type="csv")
if data:
    st.session_state["df"] = pd.read_csv(data)
    with st.expander("原始数据"):
        st.dataframe(st.session_state["df"])

query = st.text_area("请输入你关于以上表格的问题，或数据提取请求，或可视化要求：")
if query:
    # 每次输入新内容，先清空旧的可视化状态
    st.session_state["visual_type"] = None
    # 重新检测当前问题是否包含可视化指令
    for key in VISUAL_TYPES.keys():
        if key in query:
            st.session_state["visual_type"] = key
            break
else:
    st.session_state["visual_type"] = None

button = st.button("生成回答")

# 第一步：检测可视化指令，提前初始化可视化类型（非按钮点击时也检测）
if "df" in st.session_state and query:
    for key in VISUAL_TYPES.keys():
        if key in query:
            st.session_state["visual_type"] = key
            break
else:
    st.session_state["visual_type"] = None

# 第二步：如果检测到可视化类型，先展示X/Y轴选择框（常驻，可交互）
if st.session_state["visual_type"] and "df" in st.session_state:
    df = st.session_state["df"]
    cols = df.columns.tolist()
    st.subheader(f"⚙️ 配置{st.session_state['visual_type']}")
    # 选择框绑定session_state，持久化用户选择
    st.session_state["x_col"] = st.selectbox("选择X轴字段", cols, key="select_x")
    st.session_state["y_col"] = st.selectbox("选择Y轴字段", cols, key="select_y")


# 第三步：处理按钮点击逻辑
if button and not api_key:
    st.info("请输入你的API密钥")
if button and "df" not in st.session_state:
    st.info("请先上传数据文件")
if button and api_key and "df" in st.session_state:
    with st.spinner("AI正在思考中，请稍等..."):
        try:
            # 可视化请求（已提前配置X/Y轴）
            if st.session_state["visual_type"]:
                if not st.session_state["x_col"] or not st.session_state["y_col"]:
                    st.warning("⚠️ 请先选择X轴和Y轴字段！")
                else:
                    # 生成图表
                    chart_func = VISUAL_TYPES[st.session_state["visual_type"]]
                    st.success(f"✅ {st.session_state['visual_type']}生成完成！")
                    chart_func(
                        df,
                        x=st.session_state["x_col"],
                        y=st.session_state["y_col"],
                        use_container_width=True
                    )
                    # 生成图表后清空visual_type，避免残留
                    st.session_state["visual_type"] = None

            else: # 原有逻辑：文本/数据回答
                response= dataframe_agent(api_key, st.session_state["df"], query)
                if response: # 将结果渲染到网页
                    st.success("✅ 回答生成完成！")
                    # 优化：解析JSON格式的返回结果，只提取output纯文本
                    final_response = ""
                    if isinstance(response, str):
                        # 尝试解析JSON字符串（处理各种格式问题）
                        try:
                            # 去除字符串两端的空白字符（包括换行、空格）
                            clean_response = response.strip()
                            response_json = json.loads(clean_response)
                            # 提取output字段（核心修改：只保留output内容）
                            if "output" in response_json:
                                final_response = response_json["output"]
                            else:
                                # 没有output字段则使用整个JSON的字符串形式
                                final_response = json.dumps(response_json, ensure_ascii=False)
                        except json.JSONDecodeError as e:
                            # 不是JSON格式，保持原字符串不变
                            final_response = response
                    elif isinstance(response, dict):
                        # 如果直接返回字典，优先提取output
                        final_response = response.get("output", json.dumps(response, ensure_ascii=False))
                    elif isinstance(response, pd.DataFrame):
                        # 数据框类型直接赋值
                        final_response = response
                    else:
                        # 其他类型转为字符串
                        final_response = str(response)
                    # 根据final_response类型展示（文本/图表/数据框）
                    if isinstance(final_response, pd.DataFrame):
                        st.dataframe(final_response)  # 展示数据框
                    else:
                        st.markdown(final_response)  # 直接展示纯文本（核心修改）
                else:
                    st.warning("⚠️ 未生成有效回答，请检查问题或数据")

        except Exception as e: # 增加异常捕获机制
            st.error(f"❌ 生成失败：{str(e)}")
            # 可选：打印详细异常到控制台（便于开发调试）
            import traceback

            traceback.print_exc()

