#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
B站批量视频上传工具
基于biliup项目，支持批量上传本地文件夹中的视频文件到B站

Author: AI Assistant
Version: 1.0.0
Date: 2024-08-24
"""

import os
import sys
import json
import time
import logging
import argparse
import threading
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, as_completed

# 导入biliup相关模块
from biliup.plugins.bili_webup import BiliBili, Data


@dataclass
class VideoFile:
    """视频文件信息"""
    filepath: str
    filename: str
    size: int
    duration: Optional[float] = None
    upload_status: str = "待上传"  # 待上传、上传中、上传成功、上传失败
    upload_time: Optional[datetime] = None
    error_message: Optional[str] = None
    retry_count: int = 0


@dataclass
class UploadConfig:
    """上传配置"""
    # B站认证信息
    cookies: Dict = field(default_factory=dict)
    access_token: str = ""
    
    # 上传设置
    copyright: int = 2  # 1-自制, 2-转载
    tid: int = 171  # 分区ID，默认为电子竞技
    tags: List[str] = field(default_factory=lambda: ["biliup", "批量上传"])
    description: str = "通过批量上传工具上传"
    dynamic: str = ""
    
    # 技术参数
    lines: str = "AUTO"  # 上传线路
    threads: int = 3  # 并发线程数
    max_retries: int = 3  # 最大重试次数
    
    # 文件过滤
    video_extensions: List[str] = field(default_factory=lambda: ['.mp4', '.avi', '.mkv', '.mov', '.flv', '.wmv', '.webm'])
    min_file_size: int = 1024 * 1024  # 最小文件大小 1MB
    max_file_size: int = 8 * 1024 * 1024 * 1024  # 最大文件大小 8GB


class BatchBilibiliUploader:
    """B站批量上传工具主类"""
    
    def __init__(self, config_path: str = "upload_config.json"):
        self.config_path = config_path
        self.config = UploadConfig()
        self.video_files: List[VideoFile] = []
        self.upload_stats = {
            "total": 0,
            "success": 0,
            "failed": 0,
            "skipped": 0
        }
        
        # 设置日志
        self._setup_logging()
        
        # 加载配置
        self.load_config()
    
    def _setup_logging(self):
        """设置日志记录"""
        log_format = '%(asctime)s - %(levelname)s - %(message)s'
        logging.basicConfig(
            level=logging.INFO,
            format=log_format,
            handlers=[
                logging.FileHandler(f'upload_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log', encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def load_config(self):
        """加载配置文件"""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                
                # 更新配置
                for key, value in config_data.items():
                    if hasattr(self.config, key):
                        setattr(self.config, key, value)
                
                self.logger.info(f"配置文件加载成功: {self.config_path}")
            except Exception as e:
                self.logger.warning(f"配置文件加载失败: {e}，将使用默认配置")
        else:
            self.logger.info("配置文件不存在，将创建默认配置文件")
            self.save_config()
    
    def save_config(self):
        """保存配置文件"""
        try:
            config_data = {
                'cookies': self.config.cookies,
                'access_token': self.config.access_token,
                'copyright': self.config.copyright,
                'tid': self.config.tid,
                'tags': self.config.tags,
                'description': self.config.description,
                'dynamic': self.config.dynamic,
                'lines': self.config.lines,
                'threads': self.config.threads,
                'max_retries': self.config.max_retries,
                'video_extensions': self.config.video_extensions,
                'min_file_size': self.config.min_file_size,
                'max_file_size': self.config.max_file_size
            }
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"配置文件保存成功: {self.config_path}")
        except Exception as e:
            self.logger.error(f"配置文件保存失败: {e}")
    
    def scan_video_files(self, folder_path: str) -> List[VideoFile]:
        """扫描文件夹中的视频文件"""
        self.logger.info(f"开始扫描文件夹: {folder_path}")
        video_files = []
        
        if not os.path.exists(folder_path):
            self.logger.error(f"文件夹不存在: {folder_path}")
            return video_files
        
        folder_path = Path(folder_path)
        
        # 递归搜索视频文件
        for file_path in folder_path.rglob("*"):
            if file_path.is_file():
                # 检查文件扩展名
                if file_path.suffix.lower() in self.config.video_extensions:
                    try:
                        file_size = file_path.stat().st_size
                        
                        # 检查文件大小
                        if file_size < self.config.min_file_size:
                            self.logger.warning(f"文件太小，跳过: {file_path} ({file_size} bytes)")
                            continue
                        
                        if file_size > self.config.max_file_size:
                            self.logger.warning(f"文件太大，跳过: {file_path} ({file_size} bytes)")
                            continue
                        
                        video_file = VideoFile(
                            filepath=str(file_path),
                            filename=file_path.name,
                            size=file_size
                        )
                        
                        video_files.append(video_file)
                        self.logger.info(f"发现视频文件: {file_path.name} ({self._format_size(file_size)})")
                        
                    except Exception as e:
                        self.logger.error(f"处理文件时出错: {file_path}, 错误: {e}")
        
        self.logger.info(f"扫描完成，共发现 {len(video_files)} 个视频文件")
        return video_files
    
    def _format_size(self, size: int) -> str:
        """格式化文件大小显示"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"
    
    def upload_single_video(self, video_file: VideoFile) -> bool:
        """上传单个视频文件"""
        self.logger.info(f"开始上传: {video_file.filename}")
        video_file.upload_status = "上传中"
        
        try:
            # 创建视频数据对象
            video = Data()
            video.title = os.path.splitext(video_file.filename)[0][:80]  # B站标题限制80字符
            video.desc = self.config.description
            video.dynamic = self.config.dynamic
            video.copyright = self.config.copyright
            video.tid = self.config.tid
            video.set_tag(self.config.tags)
            
            # 使用BiliBili上传
            with BiliBili(video) as bili:
                # 登录
                if self.config.cookies:
                    bili.login_by_cookies(self.config.cookies)
                elif self.config.access_token:
                    bili.access_token = self.config.access_token
                else:
                    raise Exception("未配置B站登录信息")
                
                # 上传视频文件
                video_part = bili.upload_file(
                    video_file.filepath, 
                    lines=self.config.lines, 
                    tasks=self.config.threads
                )
                video.append(video_part)
                
                # 提交视频
                result = bili.submit()
                
                if result:
                    video_file.upload_status = "上传成功"
                    video_file.upload_time = datetime.now()
                    self.upload_stats["success"] += 1
                    self.logger.info(f"上传成功: {video_file.filename}")
                    return True
                else:
                    raise Exception("提交视频失败")
                    
        except Exception as e:
            video_file.upload_status = "上传失败"
            video_file.error_message = str(e)
            video_file.retry_count += 1
            self.upload_stats["failed"] += 1
            self.logger.error(f"上传失败: {video_file.filename}, 错误: {e}")
            return False
    
    def batch_upload(self, folder_path: str, concurrent_uploads: int = 1):
        """批量上传视频文件"""
        self.logger.info("=" * 50)
        self.logger.info("开始批量上传任务")
        self.logger.info("=" * 50)
        
        # 扫描视频文件
        self.video_files = self.scan_video_files(folder_path)
        
        if not self.video_files:
            self.logger.warning("未发现任何视频文件，上传任务结束")
            return
        
        self.upload_stats["total"] = len(self.video_files)
        
        # 显示上传计划
        self.logger.info(f"计划上传 {len(self.video_files)} 个视频文件:")
        for i, video_file in enumerate(self.video_files, 1):
            self.logger.info(f"  {i:2d}. {video_file.filename} ({self._format_size(video_file.size)})")
        
        # 询问用户确认
        if not self._confirm_upload():
            self.logger.info("用户取消上传任务")
            return
        
        # 开始批量上传
        start_time = time.time()
        
        if concurrent_uploads > 1:
            # 并发上传
            self.logger.info(f"使用 {concurrent_uploads} 个线程并发上传")
            self._concurrent_upload(concurrent_uploads)
        else:
            # 顺序上传
            self.logger.info("开始顺序上传")
            self._sequential_upload()
        
        # 显示上传结果
        end_time = time.time()
        self._show_upload_results(end_time - start_time)
    
    def _confirm_upload(self) -> bool:
        """确认是否开始上传"""
        try:
            confirm = input("\n是否开始上传? (y/n): ").lower().strip()
            return confirm in ['y', 'yes', '是', '确定']
        except KeyboardInterrupt:
            return False
    
    def _sequential_upload(self):
        """顺序上传"""
        for i, video_file in enumerate(self.video_files, 1):
            self.logger.info(f"[{i}/{len(self.video_files)}] 正在处理: {video_file.filename}")
            
            retry_count = 0
            while retry_count <= self.config.max_retries:
                if self.upload_single_video(video_file):
                    break
                
                retry_count += 1
                if retry_count <= self.config.max_retries:
                    self.logger.info(f"第 {retry_count} 次重试: {video_file.filename}")
                    time.sleep(5)  # 等待5秒后重试
    
    def _concurrent_upload(self, max_workers: int):
        """并发上传"""
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交所有上传任务
            future_to_video = {
                executor.submit(self._upload_with_retry, video_file): video_file 
                for video_file in self.video_files
            }
            
            # 处理完成的任务
            for future in as_completed(future_to_video):
                video_file = future_to_video[future]
                try:
                    future.result()  # 获取结果，如果有异常会抛出
                except Exception as e:
                    self.logger.error(f"并发上传异常: {video_file.filename}, 错误: {e}")
    
    def _upload_with_retry(self, video_file: VideoFile):
        """带重试机制的上传"""
        retry_count = 0
        while retry_count <= self.config.max_retries:
            if self.upload_single_video(video_file):
                return
            
            retry_count += 1
            if retry_count <= self.config.max_retries:
                self.logger.info(f"第 {retry_count} 次重试: {video_file.filename}")
                time.sleep(5)
    
    def _show_upload_results(self, duration: float):
        """显示上传结果统计"""
        self.logger.info("=" * 50)
        self.logger.info("上传任务完成")
        self.logger.info("=" * 50)
        self.logger.info(f"总计视频: {self.upload_stats['total']}")
        self.logger.info(f"上传成功: {self.upload_stats['success']}")
        self.logger.info(f"上传失败: {self.upload_stats['failed']}")
        self.logger.info(f"跳过文件: {self.upload_stats['skipped']}")
        self.logger.info(f"总用时: {duration:.2f} 秒")
        self.logger.info("=" * 50)
        
        # 显示详细结果
        if self.video_files:
            self.logger.info("\n详细结果:")
            for video_file in self.video_files:
                status_icon = "✓" if video_file.upload_status == "上传成功" else "✗"
                self.logger.info(f"  {status_icon} {video_file.filename} - {video_file.upload_status}")
                if video_file.error_message:
                    self.logger.info(f"    错误: {video_file.error_message}")
    
    def setup_credentials(self):
        """设置B站登录凭据"""
        print("B站登录凭据设置")
        print("请选择登录方式:")
        print("1. 使用cookies (推荐)")
        print("2. 使用access_token")
        
        choice = input("请选择 (1/2): ").strip()
        
        if choice == "1":
            self._setup_cookies()
        elif choice == "2":
            self._setup_access_token()
        else:
            print("无效选择")
            return
        
        self.save_config()
        print("凭据设置完成")
    
    def _setup_cookies(self):
        """设置cookies"""
        print("\n请输入B站cookies信息:")
        print("可以通过浏览器开发者工具获取，或使用biliup-rs工具获取")
        
        required_cookies = ['SESSDATA', 'bili_jct', 'DedeUserID', 'DedeUserID__ckMd5']
        cookies = {}
        
        for cookie_name in required_cookies:
            value = input(f"{cookie_name}: ").strip()
            if value:
                cookies[cookie_name] = value
        
        if len(cookies) >= 2:  # 至少需要SESSDATA和bili_jct
            self.config.cookies = cookies
            print("Cookies设置成功")
        else:
            print("Cookies信息不完整")
    
    def _setup_access_token(self):
        """设置access_token"""
        token = input("请输入access_token: ").strip()
        if token:
            self.config.access_token = token
            print("Access token设置成功")
        else:
            print("Access token不能为空")


def main():
    """主程序入口"""
    parser = argparse.ArgumentParser(description="B站批量视频上传工具")
    parser.add_argument("folder", nargs="?", help="要上传的视频文件夹路径")
    parser.add_argument("-c", "--config", default="upload_config.json", help="配置文件路径")
    parser.add_argument("-t", "--threads", type=int, default=1, help="并发上传线程数")
    parser.add_argument("--setup", action="store_true", help="设置B站登录凭据")
    parser.add_argument("--scan-only", action="store_true", help="仅扫描文件，不上传")
    
    args = parser.parse_args()
    
    # 创建上传器实例
    uploader = BatchBilibiliUploader(args.config)
    
    if args.setup:
        # 设置凭据
        uploader.setup_credentials()
        return
    
    if not args.folder:
        print("错误: 请指定要上传的视频文件夹路径")
        print("使用 --help 查看帮助信息")
        return
    
    if args.scan_only:
        # 仅扫描文件
        video_files = uploader.scan_video_files(args.folder)
        print(f"共发现 {len(video_files)} 个视频文件")
        for video_file in video_files:
            print(f"  - {video_file.filename} ({uploader._format_size(video_file.size)})")
        return
    
    # 检查登录凭据
    if not uploader.config.cookies and not uploader.config.access_token:
        print("错误: 未设置B站登录凭据")
        print("请先运行: python batch_bilibili_uploader.py --setup")
        return
    
    # 开始批量上传
    try:
        uploader.batch_upload(args.folder, args.threads)
    except KeyboardInterrupt:
        print("\n用户中断上传任务")
    except Exception as e:
        print(f"上传过程中出现错误: {e}")


if __name__ == "__main__":
    main()