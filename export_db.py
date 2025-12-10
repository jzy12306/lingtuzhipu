#!/usr/bin/env python3
"""
数据库导出脚本
本项目使用MongoDB（主数据库）和Neo4j（图数据库），不使用传统关系型数据库
本脚本提供：
1. MongoDB数据导出为JSON
2. Neo4j数据导出为Cypher语句
3. MongoDB数据转换为SQL语句的示例
"""

import os
import json
import subprocess
from datetime import datetime

def run_command(cmd, description):
    """执行命令并返回结果"""
    print(f"\n{description}...")
    print(f"执行命令: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(f"成功: {result.stdout}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"失败: {e.stderr}")
        return False
    except FileNotFoundError:
        print(f"错误: 命令 {' '.join(cmd[:1])} 未找到")
        return False

def export_mongodb_to_json():
    """导出MongoDB数据为JSON格式"""
    print("\n=== 导出MongoDB数据 ===")
    
    # MongoDB连接信息
    mongo_uri = "mongodb://localhost:27017"
    db_name = "knowledge_graph"
    
    # 导出目录
    export_dir = f"mongodb_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    os.makedirs(export_dir, exist_ok=True)
    
    # 集合列表
    collections = ["users", "documents", "entities", "relations", "configs"]
    
    for collection in collections:
        cmd = [
            "mongoexport",
            "--uri", mongo_uri,
            "--db", db_name,
            "--collection", collection,
            "--out", f"{export_dir}/{collection}.json",
            "--jsonArray"
        ]
        run_command(cmd, f"导出集合 {collection}")
    
    print(f"\nMongoDB导出完成，文件保存到: {export_dir}")
    return export_dir

def export_neo4j_to_cypher():
    """导出Neo4j数据为Cypher语句"""
    print("\n=== 导出Neo4j数据 ===")
    
    # Neo4j连接信息
    neo4j_uri = "neo4j://localhost:7687"
    neo4j_user = "neo4j"
    neo4j_password = "password"
    
    # 导出文件
    export_file = f"neo4j_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.cypher"
    
    # 使用neo4j-admin命令导出（需要Neo4j停止运行）
    cmd = [
        "neo4j-admin",
        "dump",
        "--database=neo4j",
        "--to=dump_file.dump"
    ]
    
    print("注意: neo4j-admin dump 命令需要Neo4j停止运行")
    print("如果Neo4j正在运行，请先停止它，然后再运行此脚本")
    
    # 或者使用apoc.export.cypher.all过程（需要安装APOC插件）
    print("\n备选方案: 使用APOC插件导出Cypher语句（Neo4j需运行）")
    print("需要先安装APOC插件，然后执行以下Cypher命令:")
    print("CALL apoc.export.cypher.all('neo4j_export.cypher', {format: 'cypher-shell'})")
    
    # 创建一个示例Cypher导出脚本
    with open(export_file, 'w') as f:
        f.write("// Neo4j导出Cypher语句示例\n")
        f.write("// 使用APOC插件执行以下命令导出完整数据:\n")
        f.write("// CALL apoc.export.cypher.all('neo4j_data.cypher', {format: 'cypher-shell'})\n\n")
    
    print(f"\nNeo4j导出说明已保存到: {export_file}")
    return export_file

def convert_mongodb_to_sql(mongodb_export_dir):
    """将MongoDB JSON数据转换为SQL语句"""
    print(f"\n=== 将MongoDB数据转换为SQL ===")
    print(f"使用导出目录: {mongodb_export_dir}")
    
    sql_export_file = f"sql_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql"
    
    with open(sql_export_file, 'w') as sql_file:
        # 写入SQL头部
        sql_file.write(f"-- 数据库导出SQL\n")
        sql_file.write(f"-- 导出时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        sql_file.write(f"-- 来源: MongoDB 数据库 'knowledge_graph'\n\n")
        
        # 集合映射到表
        collections = ["users", "documents", "entities", "relations"]
        
        for collection in collections:
            json_file = os.path.join(mongodb_export_dir, f"{collection}.json")
            if not os.path.exists(json_file):
                print(f"跳过 {collection}: 文件不存在")
                continue
            
            print(f"转换 {collection} 到SQL...")
            
            # 读取JSON数据
            with open(json_file, 'r') as f:
                data = json.load(f)
            
            if not data:
                print(f"{collection}: 没有数据")
                continue
            
            # 生成CREATE TABLE语句
            if data:
                sample = data[0]
                # 简化的字段类型映射
                field_types = {}
                for key, value in sample.items():
                    if isinstance(value, str):
                        field_types[key] = "VARCHAR(255)"
                    elif isinstance(value, int):
                        field_types[key] = "INT"
                    elif isinstance(value, float):
                        field_types[key] = "FLOAT"
                    elif isinstance(value, bool):
                        field_types[key] = "BOOLEAN"
                    else:
                        field_types[key] = "JSON"
                
                # 写入CREATE TABLE
                sql_file.write(f"-- 创建 {collection} 表\n")
                sql_file.write(f"CREATE TABLE IF NOT EXISTS {collection} (\n")
                sql_file.write(f"    _id VARCHAR(255) PRIMARY KEY,\n")
                
                # 其他字段
                fields = []
                for field, type_ in field_types.items():
                    if field != "_id":
                        fields.append(f"    {field} {type_}")
                
                sql_file.write(",\n".join(fields))
                sql_file.write("\n);\n\n")
                
                # 生成INSERT语句
                sql_file.write(f"-- 插入 {collection} 数据\n")
                for item in data:
                    keys = []
                    values = []
                    
                    for key, value in item.items():
                        keys.append(key)
                        if isinstance(value, str):
                            # 转义单引号
                            escaped = value.replace("'", "''")
                            values.append(f"'{escaped}'")
                        elif isinstance(value, bool):
                            values.append("TRUE" if value else "FALSE")
                        elif value is None:
                            values.append("NULL")
                        elif isinstance(value, (dict, list)):
                            # JSON类型
                            escaped = json.dumps(value).replace("'", "''")
                            values.append(f"'{escaped}'")
                        else:
                            values.append(str(value))
                    
                    sql_file.write(f"INSERT INTO {collection} ({', '.join(keys)}) VALUES ({', '.join(values)});\n")
                
                sql_file.write("\n")
    
    print(f"\nSQL转换完成，文件保存到: {sql_export_file}")
    return sql_export_file

def main():
    """主函数"""
    print("=" * 60)
    print("项目数据库导出工具")
    print("=" * 60)
    print("本项目使用的数据库:")
    print("1. MongoDB（主数据库）: 存储用户、文档、实体、关系等")
    print("2. Neo4j（图数据库）: 存储知识图谱数据")
    print("3. 无传统关系型数据库（无SQL文件）")
    print("=" * 60)
    
    # 自动执行所有导出操作（无需用户输入）
    print("\n自动执行所有导出操作...")
    
    mongodb_dir = export_mongodb_to_json()
    export_neo4j_to_cypher()
    convert_mongodb_to_sql(mongodb_dir)
    
    print("\n" + "=" * 60)
    print("导出操作完成")
    print("=" * 60)

if __name__ == "__main__":
    main()
