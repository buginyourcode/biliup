#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
B站批量上传工具测试脚本

测试各个模块的功能，确保程序正常工作
"""

import os
import sys
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

# 导入要测试的模块
from batch_bilibili_uploader import BatchBilibiliUploader, VideoFile, UploadConfig


class TestBatchBilibiliUploader(unittest.TestCase):
    """批量上传工具测试类"""
    
    def setUp(self):
        """测试前准备"""
        # 创建临时配置文件
        self.temp_dir = tempfile.mkdtemp()
        self.config_file = os.path.join(self.temp_dir, "test_config.json")
        
        # 创建上传器实例
        self.uploader = BatchBilibiliUploader(self.config_file)
    
    def tearDown(self):
        """测试后清理"""
        # 清理临时文件
        if os.path.exists(self.config_file):
            os.remove(self.config_file)
        os.rmdir(self.temp_dir)
    
    def test_config_creation(self):
        """测试配置文件创建"""
        # 检查配置对象
        self.assertIsInstance(self.uploader.config, UploadConfig)
        
        # 检查默认值
        self.assertEqual(self.uploader.config.copyright, 2)
        self.assertEqual(self.uploader.config.tid, 171)
        self.assertEqual(self.uploader.config.threads, 3)
        self.assertEqual(self.uploader.config.max_retries, 3)
    
    def test_config_save_load(self):
        """测试配置文件保存和加载"""
        # 修改配置
        self.uploader.config.tid = 17
        self.uploader.config.tags = ["测试", "自动化"]
        self.uploader.config.description = "测试描述"
        
        # 保存配置
        self.uploader.save_config()
        
        # 检查文件是否创建
        self.assertTrue(os.path.exists(self.config_file))
        
        # 创建新实例并加载配置
        new_uploader = BatchBilibiliUploader(self.config_file)
        
        # 验证配置是否正确加载
        self.assertEqual(new_uploader.config.tid, 17)
        self.assertEqual(new_uploader.config.tags, ["测试", "自动化"])
        self.assertEqual(new_uploader.config.description, "测试描述")
    
    def test_video_file_creation(self):
        """测试VideoFile对象创建"""
        video_file = VideoFile(
            filepath="/test/video.mp4",
            filename="video.mp4",
            size=1024000
        )
        
        self.assertEqual(video_file.filepath, "/test/video.mp4")
        self.assertEqual(video_file.filename, "video.mp4")
        self.assertEqual(video_file.size, 1024000)
        self.assertEqual(video_file.upload_status, "待上传")
        self.assertEqual(video_file.retry_count, 0)
    
    def test_format_size(self):
        """测试文件大小格式化"""
        # 测试不同大小的格式化
        self.assertEqual(self.uploader._format_size(1024), "1.0 KB")
        self.assertEqual(self.uploader._format_size(1024 * 1024), "1.0 MB")
        self.assertEqual(self.uploader._format_size(1024 * 1024 * 1024), "1.0 GB")
        
        # 测试小数
        self.assertEqual(self.uploader._format_size(1536), "1.5 KB")  # 1.5KB
    
    def test_scan_video_files_empty_folder(self):
        """测试扫描空文件夹"""
        # 创建临时空文件夹
        empty_folder = os.path.join(self.temp_dir, "empty")
        os.makedirs(empty_folder)
        
        # 扫描文件
        video_files = self.uploader.scan_video_files(empty_folder)
        
        # 应该返回空列表
        self.assertEqual(len(video_files), 0)
        
        # 清理
        os.rmdir(empty_folder)
    
    def test_scan_video_files_with_videos(self):
        """测试扫描包含视频的文件夹"""
        # 创建测试文件夹
        test_folder = os.path.join(self.temp_dir, "videos")
        os.makedirs(test_folder)
        
        # 创建模拟视频文件
        test_files = [
            "video1.mp4",
            "video2.avi", 
            "video3.mkv",
            "not_video.txt",  # 非视频文件
            "small.mp4"       # 会创建为小文件
        ]
        
        for filename in test_files:
            filepath = os.path.join(test_folder, filename)
            with open(filepath, 'wb') as f:
                if filename == "small.mp4":
                    f.write(b'x' * 100)  # 100字节，小于最小限制
                else:
                    f.write(b'x' * (2 * 1024 * 1024))  # 2MB
        
        # 扫描文件
        video_files = self.uploader.scan_video_files(test_folder)
        
        # 检查结果 (应该有3个有效视频文件，排除txt和小文件)
        self.assertEqual(len(video_files), 3)
        
        # 检查文件名
        found_names = [vf.filename for vf in video_files]
        self.assertIn("video1.mp4", found_names)
        self.assertIn("video2.avi", found_names)
        self.assertIn("video3.mkv", found_names)
        self.assertNotIn("not_video.txt", found_names)
        self.assertNotIn("small.mp4", found_names)  # 太小被过滤
        
        # 清理测试文件
        for filename in test_files:
            os.remove(os.path.join(test_folder, filename))
        os.rmdir(test_folder)
    
    def test_scan_nonexistent_folder(self):
        """测试扫描不存在的文件夹"""
        nonexistent = "/path/that/does/not/exist"
        video_files = self.uploader.scan_video_files(nonexistent)
        
        # 应该返回空列表
        self.assertEqual(len(video_files), 0)
    
    @patch('batch_bilibili_uploader.BiliBili')
    def test_upload_single_video_success(self, mock_bilibili):
        """测试单个视频上传成功"""
        # 模拟BiliBili上传成功
        mock_bili_instance = MagicMock()
        mock_bili_instance.upload_file.return_value = {"title": "test_video", "filename": "test.mp4"}
        mock_bili_instance.submit.return_value = {"code": 0, "message": "success"}
        mock_bilibili.return_value.__enter__.return_value = mock_bili_instance
        
        # 设置模拟cookies
        self.uploader.config.cookies = {
            'SESSDATA': 'test_sessdata',
            'bili_jct': 'test_bili_jct'
        }
        
        # 创建测试视频文件对象
        video_file = VideoFile(
            filepath="/test/video.mp4",
            filename="video.mp4",
            size=10000000
        )
        
        # 执行上传
        result = self.uploader.upload_single_video(video_file)
        
        # 验证结果
        self.assertTrue(result)
        self.assertEqual(video_file.upload_status, "上传成功")
        self.assertIsNotNone(video_file.upload_time)
    
    @patch('batch_bilibili_uploader.BiliBili')
    def test_upload_single_video_failure(self, mock_bilibili):
        """测试单个视频上传失败"""
        # 模拟BiliBili上传失败
        mock_bilibili.side_effect = Exception("网络错误")
        
        # 设置模拟cookies
        self.uploader.config.cookies = {
            'SESSDATA': 'test_sessdata',
            'bili_jct': 'test_bili_jct'
        }
        
        # 创建测试视频文件对象
        video_file = VideoFile(
            filepath="/test/video.mp4",
            filename="video.mp4",
            size=10000000
        )
        
        # 执行上传
        result = self.uploader.upload_single_video(video_file)
        
        # 验证结果
        self.assertFalse(result)
        self.assertEqual(video_file.upload_status, "上传失败")
        self.assertIsNotNone(video_file.error_message)
        self.assertEqual(video_file.retry_count, 1)


class TestUploadConfig(unittest.TestCase):
    """上传配置测试类"""
    
    def test_default_values(self):
        """测试默认值"""
        config = UploadConfig()
        
        self.assertEqual(config.copyright, 2)
        self.assertEqual(config.tid, 171)
        self.assertEqual(config.threads, 3)
        self.assertEqual(config.max_retries, 3)
        self.assertIn('.mp4', config.video_extensions)
        self.assertEqual(config.min_file_size, 1024 * 1024)
        self.assertEqual(config.max_file_size, 8 * 1024 * 1024 * 1024)


def create_test_environment():
    """创建测试环境"""
    print("创建测试环境...")
    
    # 创建测试文件夹
    test_dir = "test_videos"
    os.makedirs(test_dir, exist_ok=True)
    
    # 创建一些测试视频文件（空文件）
    test_files = [
        "游戏录播_王者荣耀.mp4",
        "教程视频_Python编程.avi",
        "生活Vlog_日常.mkv",
        "音乐MV_新歌发布.mp4",
        "small_file.mp4",  # 小文件
        "document.txt"     # 非视频文件
    ]
    
    for filename in test_files:
        filepath = os.path.join(test_dir, filename)
        with open(filepath, 'wb') as f:
            if filename == "small_file.mp4":
                f.write(b'x' * 100)  # 小文件
            elif filename == "document.txt":
                f.write(b'This is not a video file')
            else:
                f.write(b'x' * (5 * 1024 * 1024))  # 5MB
    
    print(f"测试文件创建完成，位于: {os.path.abspath(test_dir)}")
    return test_dir


def cleanup_test_environment(test_dir):
    """清理测试环境"""
    if os.path.exists(test_dir):
        for file in os.listdir(test_dir):
            os.remove(os.path.join(test_dir, file))
        os.rmdir(test_dir)
        print("测试环境清理完成")


def main():
    """主测试函数"""
    print("B站批量上传工具测试")
    print("=" * 50)
    
    # 运行单元测试
    print("1. 运行单元测试...")
    unittest.main(argv=[''], exit=False, verbosity=2)
    
    print("\n" + "=" * 50)
    print("2. 功能测试...")
    
    # 创建测试环境
    test_dir = create_test_environment()
    
    try:
        # 测试扫描功能
        print("\n测试文件扫描功能:")
        uploader = BatchBilibiliUploader("test_config.json")
        video_files = uploader.scan_video_files(test_dir)
        
        print(f"扫描结果: 发现 {len(video_files)} 个视频文件")
        for video_file in video_files:
            print(f"  - {video_file.filename} ({uploader._format_size(video_file.size)})")
        
        # 测试配置保存
        print("\n测试配置保存:")
        uploader.config.tags = ["测试", "自动化"]
        uploader.save_config()
        print("配置保存成功")
        
        # 测试配置加载
        print("\n测试配置加载:")
        new_uploader = BatchBilibiliUploader("test_config.json")
        print(f"加载的标签: {new_uploader.config.tags}")
        
        print("\n功能测试完成 ✓")
        
    except Exception as e:
        print(f"\n功能测试失败: {e}")
    
    finally:
        # 清理测试环境
        cleanup_test_environment(test_dir)
        if os.path.exists("test_config.json"):
            os.remove("test_config.json")


if __name__ == "__main__":
    main()