"""测试配置和固件"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock


@pytest.fixture
def event_loop():
    """创建事件循环"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_service_factory():
    """服务工厂的mock"""
    from unittest.mock import patch
    with patch('src.services.service_factory.ServiceFactory') as mock:
        yield mock


@pytest.fixture
def sample_user_data():
    """示例用户数据"""
    return {
        "username": "testuser",
        "email": "test@example.com",
        "password": "TestPassword123",
        "full_name": "Test User"
    }


@pytest.fixture
def sample_document_data():
    """示例文档数据"""
    return {
        "title": "Test Document",
        "content": "This is a test document content.",
        "document_type": "markdown",
        "filename": "test.md"
    }
