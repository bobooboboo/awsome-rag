from typing import List, Dict, Optional

from llama_index.core import Settings
from llama_index.core.llms import ChatMessage, MessageRole, LLM
from llama_index.llms.dashscope import DashScope
from llama_index.llms.huggingface import HuggingFaceLLM

from app.config.config import (
    CHAT_MODEL_TYPE,
    LOCAL_CHAT_MODEL_CONFIG,
    ALIYUN_CHAT_MODEL_CONFIG
)


class BaseChatModel:
    """
    聊天模型基类，定义聊天接口并实现共用逻辑
    """

    _llm: LLM = None

    def __init__(self, model_name: str):
        self._model_name = model_name

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def llm(self) -> LLM:
        return self._llm

    @staticmethod
    def _convert_to_chat_messages(msg_list: List[Dict[str, str]]) -> List[ChatMessage]:
        chat_messages = []
        for msg in msg_list:
            role = msg["role"]
            content = msg["content"]

            if role == "user":
                role = MessageRole.USER
            elif role == "assistant":
                role = MessageRole.ASSISTANT
            elif role == "system":
                role = MessageRole.SYSTEM
            else:
                print(f"警告: 未知的角色类型 {role}，使用USER角色替代")
                role = MessageRole.USER

            chat_messages.append(ChatMessage(role=role, content=content))
        return chat_messages

    def chat(self, chat_input: List[Dict[str, str]], **kwargs) -> str:
        if self._llm is None:
            raise ValueError("模型未初始化")

        chat_messages = self._convert_to_chat_messages(chat_input)
        result = self._llm.chat(chat_messages, **kwargs)
        return result.message.content

    def generate(self, input_prompt: str, **kwargs) -> str:
        if self._llm is None:
            raise ValueError("模型未初始化")

        result = self._llm.complete(input_prompt, **kwargs)
        return result.text

    def set_as_default(self) -> 'BaseChatModel':
        if self._llm is not None:
            Settings.llm = self._llm
        return self


class LocalChatModel(BaseChatModel):
    """
    本地聊天模型封装类，使用HuggingFace模型
    """

    def __init__(
            self,
            model_name: Optional[str] = None,
            temperature: Optional[float] = None,
            max_tokens: Optional[int] = None,
            context_window: Optional[int] = None,
            **kwargs
    ):
        model_name = model_name or LOCAL_CHAT_MODEL_CONFIG["model_name"]
        temperature = temperature if temperature is not None else LOCAL_CHAT_MODEL_CONFIG["temperature"]
        max_tokens = max_tokens or LOCAL_CHAT_MODEL_CONFIG["max_tokens"]
        context_window = context_window or LOCAL_CHAT_MODEL_CONFIG["context_window"]

        super().__init__(model_name=model_name)

        print(f"初始化本地LLM模型，模型: {model_name}, 温度: {temperature}, 最大生成Token: {max_tokens}")

        generate_kwargs = {"temperature": temperature, "do_sample": True}

        self._llm = HuggingFaceLLM(
            model_name=model_name,
            max_new_tokens=max_tokens,
            context_window=context_window,
            tokenizer_kwargs={"trust_remote_code": True},
            model_kwargs={"trust_remote_code": True},
            generate_kwargs=generate_kwargs,
            **kwargs
        )


class AliyunChatModel(BaseChatModel):
    """
    阿里云聊天模型封装类，使用通义千问系列模型
    """

    def __init__(
            self,
            model_name: Optional[str] = None,
            api_key: Optional[str] = None,
            temperature: Optional[float] = None,
            max_tokens: Optional[int] = None,
            **kwargs
    ):
        model_name = model_name or ALIYUN_CHAT_MODEL_CONFIG["model_name"]
        api_key = api_key or ALIYUN_CHAT_MODEL_CONFIG["api_key"]
        temperature = temperature if temperature is not None else ALIYUN_CHAT_MODEL_CONFIG["temperature"]
        max_tokens = max_tokens or ALIYUN_CHAT_MODEL_CONFIG["max_tokens"]

        super().__init__(model_name=model_name)

        if not api_key:
            raise ValueError("阿里云API密钥未设置，请检查配置")

        print(f"初始化阿里云LLM模型，模型: {model_name}, API密钥前缀: {api_key[:8]}...")

        self._llm = DashScope(
            model_name=model_name,
            api_key=api_key,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )


class ChatModelFactory:
    """
    聊天模型工厂类，用于创建不同类型的聊天模型
    """

    @staticmethod
    def create() -> BaseChatModel:
        model_type = CHAT_MODEL_TYPE

        if model_type == "aliyun":
            print("使用阿里云聊天模型...")
            return AliyunChatModel()
        elif model_type == "local":
            print("使用本地聊天模型...")
            return LocalChatModel()
        else:
            raise ValueError(f"不支持的聊天模型类型: {model_type}")


def get_chat_model() -> BaseChatModel:
    return ChatModelFactory.create()


if __name__ == "__main__":
    test_msgs = [
        {"role": "system", "content": "你是一个智能助手，可以帮助用户解答问题。"},
        {"role": "user", "content": "请介绍一下中国的首都北京。"}
    ]

    import os

    os.environ["CHAT_MODEL_TYPE"] = "aliyun"

    print("\n使用阿里云聊天模型进行测试:")
    try:
        test_model = AliyunChatModel()
        print(f"模型类型: {test_model.__class__.__name__}, 模型名称: {test_model.model_name}")

        reply = test_model.chat(test_msgs)
        print("\n模型回复:")
        print(reply)

        test_prompt = "请用一句话介绍人工智能。"
        print(f"\n使用提示词: '{test_prompt}'")
        generation = test_model.generate(test_prompt)
        print("生成结果:")
        print(generation)
    except Exception as e:
        print(f"测试失败: {e}")
