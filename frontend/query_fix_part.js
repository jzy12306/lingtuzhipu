                // 调用实际的后端API
                try {
                    const response = await fetch('http://localhost:8000/api/analyst/test-query', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        credentials: 'include',
                        mode: 'cors',
                        body: JSON.stringify({ query: query })
                    });
                    const result = await response.json();
                    showQueryResultsFromAPI(result, query);
                } catch (error) {
                    console.error('查询失败:', error);
                    alert('查询失败，请稍后重试');
                }