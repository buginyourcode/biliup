#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
B站批量视频上传工具使用示例

演示如何使用BatchBilibiliUploader类进行批量上传
"""

import os
import sys
from batch_bilibili_uploader import BatchBilibiliUploader, UploadConfig


def example_basic_usage():
    """示例1: 基本使用方法"""
    print("示例1: 基本批量上传")
    print("-" * 40)
    
    # 创建上传器
    uploader = BatchBilibiliUploader("basic_config.json")
    
    # 设置基本配置
    uploader.config.copyright = 2  # 转载
    uploader.config.tid = 171  # 电子竞技分区
    uploader.config.tags = ["游戏", "录播", "biliup"]
    uploader.config.description = "游戏录播视频"
    
    # 模拟cookies (实际使用时需要真实的cookies)
    uploader.config.cookies = {
        'SESSDATA': 'your_sessdata_here',
        'bili_jct': 'your_bili_jct_here',
        'DedeUserID': 'your_userid_here',
        'DedeUserID__ckMd5': 'your_usermd5_here'
    }
    
    # 保存配置
    uploader.save_config()
    
    # 扫描文件（仅扫描，不上传）
    folder_path = "/path/to/your/videos"  # 替换为实际路径
    
    print(f"扫描文件夹: {folder_path}")
    if os.path.exists(folder_path):
        video_files = uploader.scan_video_files(folder_path)
        print(f"发现 {len(video_files)} 个视频文件")
        
        # 显示文件列表
        for video_file in video_files:
            print(f"  - {video_file.filename} ({uploader._format_size(video_file.size)})")
    else:
        print("文件夹不存在，请修改folder_path")


def example_custom_config():
    """示例2: 自定义配置"""
    print("示例2: 自定义配置上传")
    print("-" * 40)
    
    # 创建自定义配置
    config = UploadConfig()
    config.copyright = 1  # 自制
    config.tid = 17  # 单机游戏
    config.tags = ["我的世界", "建筑", "教程"]
    config.description = "我的世界建筑教程系列"
    config.dynamic = "最新一期建筑教程，欢迎大家观看！"
    config.threads = 2  # 2个线程并发上传
    config.max_retries = 5  # 最多重试5次
    
    # 只支持mp4格式
    config.video_extensions = ['.mp4']
    config.min_file_size = 10 * 1024 * 1024  # 最小10MB
    config.max_file_size = 2 * 1024 * 1024 * 1024  # 最大2GB
    
    print("自定义配置:")
    print(f"  版权类型: {'自制' if config.copyright == 1 else '转载'}")
    print(f"  分区ID: {config.tid}")
    print(f"  标签: {', '.join(config.tags)}")
    print(f"  描述: {config.description}")
    print(f"  并发线程: {config.threads}")
    print(f"  支持格式: {', '.join(config.video_extensions)}")


def example_programmatic_upload():
    """示例3: 编程方式上传"""
    print("示例3: 编程方式批量上传")
    print("-" * 40)
    
    uploader = BatchBilibiliUploader("programmatic_config.json")
    
    # 配置上传参数
    uploader.config.copyright = 2
    uploader.config.tid = 188  # 科技数码
    uploader.config.tags = ["科技", "数码", "评测"]
    uploader.config.description = "科技产品评测视频"
    
    # 模拟已有的视频文件列表
    fake_videos = [
        "手机评测_iPhone15.mp4",
        "笔记本评测_MacBookPro.mp4", 
        "相机评测_SonyA7M4.mp4"
    ]
    
    print("模拟上传流程:")
    for i, video_name in enumerate(fake_videos, 1):
        print(f"  [{i}/{len(fake_videos)}] 处理: {video_name}")
        print(f"    - 检查文件大小...")
        print(f"    - 准备上传数据...")
        print(f"    - 上传到B站...")
        print(f"    - 上传成功 ✓")
    
    print("批量上传完成!")


def example_error_handling():
    """示例4: 错误处理和重试"""
    print("示例4: 错误处理和重试机制")
    print("-" * 40)
    
    uploader = BatchBilibiliUploader("error_handling_config.json")
    
    # 配置重试参数
    uploader.config.max_retries = 3
    uploader.config.threads = 1  # 单线程避免并发问题
    
    # 模拟上传过程中的各种情况
    scenarios = [
        ("video1.mp4", "success", "上传成功"),
        ("video2.mp4", "network_error", "网络错误，重试中..."),
        ("video3.mp4", "auth_error", "认证失败"),
        ("video4.mp4", "success_after_retry", "重试后成功"),
        ("video5.mp4", "file_too_large", "文件过大，跳过")
    ]
    
    success_count = 0
    failed_count = 0
    
    for video, status, message in scenarios:
        print(f"处理: {video}")
        
        if status == "success":
            print(f"  ✓ {message}")
            success_count += 1
        elif status == "network_error":
            print(f"  ⚠ {message}")
            for retry in range(1, 4):
                print(f"    第{retry}次重试...")
                if retry == 3:  # 第3次重试成功
                    print(f"  ✓ 重试成功")
                    success_count += 1
                    break
        elif status == "success_after_retry":
            print(f"  ⚠ 首次上传失败，重试中...")
            print(f"  ✓ {message}")
            success_count += 1
        else:
            print(f"  ✗ {message}")
            failed_count += 1
    
    print(f"\n统计结果:")
    print(f"  成功: {success_count}")
    print(f"  失败: {failed_count}")


def example_file_filtering():
    """示例5: 文件过滤"""
    print("示例5: 文件过滤规则")
    print("-" * 40)
    
    uploader = BatchBilibiliUploader()
    
    # 模拟文件夹中的文件
    mock_files = [
        ("gameplay.mp4", 500 * 1024 * 1024, True),    # 500MB MP4
        ("tutorial.avi", 1.5 * 1024 * 1024 * 1024, True),  # 1.5GB AVI
        ("small_clip.mp4", 500 * 1024, False),        # 500KB 太小
        ("huge_video.mkv", 10 * 1024 * 1024 * 1024, False), # 10GB 太大
        ("audio.mp3", 50 * 1024 * 1024, False),       # MP3 不支持
        ("normal_video.mov", 800 * 1024 * 1024, True), # 800MB MOV
    ]
    
    print("文件过滤规则:")
    print(f"  支持格式: {', '.join(uploader.config.video_extensions)}")
    print(f"  最小大小: {uploader._format_size(uploader.config.min_file_size)}")
    print(f"  最大大小: {uploader._format_size(uploader.config.max_file_size)}")
    print()
    
    valid_files = []
    
    for filename, size, should_pass in mock_files:
        size_str = uploader._format_size(size)
        
        # 检查扩展名
        ext = os.path.splitext(filename)[1].lower()
        if ext not in uploader.config.video_extensions:
            print(f"  ✗ {filename} ({size_str}) - 不支持的格式")
            continue
        
        # 检查大小
        if size < uploader.config.min_file_size:
            print(f"  ✗ {filename} ({size_str}) - 文件太小")
            continue
        
        if size > uploader.config.max_file_size:
            print(f"  ✗ {filename} ({size_str}) - 文件太大")
            continue
        
        print(f"  ✓ {filename} ({size_str}) - 通过过滤")
        valid_files.append(filename)
    
    print(f"\n过滤结果: {len(valid_files)}/{len(mock_files)} 文件通过")


def main():
    """运行所有示例"""
    examples = [
        example_basic_usage,
        example_custom_config,
        example_programmatic_upload,
        example_error_handling,
        example_file_filtering
    ]
    
    print("B站批量上传工具使用示例")
    print("=" * 50)
    
    for i, example_func in enumerate(examples, 1):
        print(f"\n{i}. {example_func.__doc__.split(':')[1].strip()}")
        try:
            example_func()
        except Exception as e:
            print(f"示例执行出错: {e}")
        
        if i < len(examples):
            print("\n" + "=" * 50)
    
    print("\n所有示例演示完成！")
    print("\n要开始实际使用，请:")
    print("1. 运行: python batch_bilibili_uploader.py --setup")
    print("2. 配置B站登录凭据")
    print("3. 运行: python batch_bilibili_uploader.py /path/to/videos")


if __name__ == "__main__":
    main()