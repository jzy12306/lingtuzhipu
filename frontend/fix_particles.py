#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
为所有HTML页面添加粒子特效初始化
"""
import os
import re

frontend_dir = r"C:\dailywork\graduation project\Lingtu\frontend"
pages = ["graph.html", "admin.html", "user-center.html"]

def add_particles_to_file(filepath):
    """为HTML文件添加initParticleSystem调用"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查是否已有initParticleSystem调用
    if 'initParticleSystem()' in content:
        print(f"✓ {os.path.basename(filepath)} 已包含initParticleSystem调用，跳过")
        return True
    
    # 查找DOMContentLoaded并添加initParticleSystem调用
    # 模式1: document.addEventListener('DOMContentLoaded', function() {
    pattern1 = r"(document\.addEventListener\('DOMContentLoaded',\s*function\(\)\s*\{)"
    replacement1 = r"\1\n            initParticleSystem();"
    
    new_content = re.sub(pattern1, replacement1, content)
    
    if new_content != content:
        # 写入文件
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"✓ {os.path.basename(filepath)} 已添�initParticleSystem() 调用")
        return True
    else:
        print(f"✗ {os.path.basename(filepath)} 未找到DOMContentLoaded，需要手动处理")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("为所有页面添加粒子特效初始化")
    print("=" * 50)
    print()
    
    all_success = True
    
    for page in pages:
        filepath = os.path.join(frontend_dir, page)
        if os.path.exists(filepath):
            success = add_particles_to_file(filepath)
            if not success:
                all_success = False
        else:
            print(f"✗ 文件不存在: {page}")
            all_success = False
    
    print()
    print("=" * 50)
    if all_success:
        print("✅ 所有页面的粒子特效已添加完成！")
    else:
        print("⚠️  部分页面需要手动处理")
    print("=" * 50)