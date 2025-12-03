// 添加公司节点
CREATE (netease:公司 {name: "网易", industry: "互联网", founded: 1997, location: "杭州"})
CREATE (tencent:公司 {name: "腾讯", industry: "互联网", founded: 1998, location: "深圳"})
CREATE (alibaba:公司 {name: "阿里巴巴", industry: "电子商务", founded: 1999, location: "杭州"})
CREATE (baidu:公司 {name: "百度", industry: "搜索引擎", founded: 2000, location: "北京"})

// 添加产品节点
CREATE (wechat:产品 {name: "微信", type: "社交应用", users: "13亿"})
CREATE (qq:产品 {name: "QQ", type: "即时通讯", users: "6亿"})
CREATE (taobao:产品 {name: "淘宝", type: "电商平台", users: "9亿"})
CREATE (dingding:产品 {name: "钉钉", type: "办公软件", users: "5亿"})
CREATE (wangyiyun:产品 {name: "网易云音乐", type: "音乐平台", users: "2亿"})

// 添加人物节点
CREATE (pony:人物 {name: "马化腾", role: "CEO", company: "腾讯"})
CREATE (jack:人物 {name: "马云", role: "创始人", company: "阿里巴巴"})
CREATE (robin:人物 {name: "李彦宏", role: "CEO", company: "百度"})
CREATE (william:人物 {name: "丁磊", role: "CEO", company: "网易"})

// 创建关系
CREATE (tencent)-[:开发 {year: 2011}]->(wechat)
CREATE (tencent)-[:开发 {year: 1999}]->(qq)
CREATE (alibaba)-[:开发 {year: 2003}]->(taobao)
CREATE (alibaba)-[:开发 {year: 2014}]->(dingding)
CREATE (netease)-[:开发 {year: 2013}]->(wangyiyun)

CREATE (pony)-[:担任 {since: 1998}]->(tencent)
CREATE (jack)-[:担任 {since: 1999}]->(alibaba)
CREATE (robin)-[:担任 {since: 2000}]->(baidu)
CREATE (william)-[:担任 {since: 1997}]->(netease)

CREATE (tencent)-[:竞争对手 {level: "高"}]->(alibaba)
CREATE (tencent)-[:合作伙伴 {type: "战略合作"}]->(netease)
CREATE (alibaba)-[:竞争对手 {level: "高"}]->(baidu)

// 添加标签信息
CREATE (ai:技术领域 {name: "人工智能", trend: "上升"})
CREATE (cloud:技术领域 {name: "云计算", trend: "稳定"})
CREATE (blockchain:技术领域 {name: "区块链", trend: "下降"})

CREATE (tencent)-[:投资 {amount: "100亿"}]->(ai)
CREATE (alibaba)-[:投资 {amount: "150亿"}]->(cloud)
CREATE (baidu)-[:研究 {level: "领先"}]->(ai)

RETURN "测试数据添加成功！共添加了 12 个节点和 15 个关系"