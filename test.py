# Prompt + LLM
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field




# 定义模型
model = ChatOpenAI(
    model = "openai/gpt-5-mini",
    api_key="sk-or-v1-",
    base_url="https://openrouter.ai/api/v1"
)

# 定义 Prompt
# prompt = ChatPromptTemplate.from_template(
#     "请用简单语言解释：{topic}"
# )

# 组合Chain（LCEL：LangChain Expression Language)
# chain = prompt | model

# 调用
#result = chain.invoke({"topic": "什么是 LangChain？"})


# 流式输出
# for chunk in chain.stream({"topic": "什么是 LangChain？"}):
#     print(chunk.content, end="", flush=True)
# print()

# Output Parser
# class Explanation(BaseModel):
#     concept: str = Field(description="概念名称")
#     explanation: str = Field(description="详细解释")
#     example: str = Field(description="举一个简单例子")

# parser = PydanticOutputParser(pydantic_object=Explanation)

# prompt = ChatPromptTemplate.from_template(
#     "请解释{topic}. \n{format_instructions}"
# )

# chain = prompt.partial(
#     format_instructions=parser.get_format_instructions()
# ) | model | parser

# result = chain.invoke({"topic": "什么是 LangChain？"})

# print(result)

# print(result.json())


# 多步骤 Chain
## Step 1: 生成解释
prompt1 = ChatPromptTemplate.from_template(
    "请解释概念：{topic}"
)

## Step 2：转成更通俗版本
prompt2 = ChatPromptTemplate.from_template(
    "把下面内容讲给小学生听： {text}"
)

chain = (
    {"text": prompt1 | model}
    | prompt2
    | model
)

result = chain.invoke({"topic": "什么是 LangChain？"})

print(result.content)