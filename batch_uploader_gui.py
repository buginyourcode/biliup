#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
B站批量视频上传工具 - GUI版本

基于tkinter的图形界面版本
"""

import os
import sys
import json
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from pathlib import Path
from datetime import datetime
import logging

# 导入主程序
from batch_bilibili_uploader import BatchBilibiliUploader, VideoFile


class UploaderGUI:
    """批量上传工具GUI界面"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("B站批量视频上传工具")
        self.root.geometry("800x600")
        self.root.resizable(True, True)
        
        # 创建上传器实例
        self.uploader = BatchBilibiliUploader()
        
        # GUI组件
        self.setup_ui()
        
        # 上传状态
        self.is_uploading = False
        self.upload_thread = None
    
    def setup_ui(self):
        """设置用户界面"""
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置网格权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(5, weight=1)
        
        # 1. 文件夹选择
        ttk.Label(main_frame, text="视频文件夹:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.folder_var = tk.StringVar()
        folder_frame = ttk.Frame(main_frame)
        folder_frame.grid(row=0, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        folder_frame.columnconfigure(0, weight=1)
        
        ttk.Entry(folder_frame, textvariable=self.folder_var, width=50).grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
        ttk.Button(folder_frame, text="浏览", command=self.browse_folder).grid(row=0, column=1)
        
        # 2. 上传设置
        settings_frame = ttk.LabelFrame(main_frame, text="上传设置", padding="5")
        settings_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        settings_frame.columnconfigure(1, weight=1)
        
        # 版权类型
        ttk.Label(settings_frame, text="版权类型:").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.copyright_var = tk.StringVar(value="转载")
        copyright_combo = ttk.Combobox(settings_frame, textvariable=self.copyright_var, values=["自制", "转载"], state="readonly")
        copyright_combo.grid(row=0, column=1, sticky=tk.W, padx=5)
        
        # 分区
        ttk.Label(settings_frame, text="投稿分区:").grid(row=0, column=2, sticky=tk.W, padx=5)
        self.tid_var = tk.StringVar(value="171")
        tid_entry = ttk.Entry(settings_frame, textvariable=self.tid_var, width=10)
        tid_entry.grid(row=0, column=3, sticky=tk.W, padx=5)
        
        # 标签
        ttk.Label(settings_frame, text="标签:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.tags_var = tk.StringVar(value="biliup,批量上传")
        ttk.Entry(settings_frame, textvariable=self.tags_var, width=30).grid(row=1, column=1, columnspan=3, sticky=(tk.W, tk.E), padx=5, pady=5)
        
        # 描述
        ttk.Label(settings_frame, text="视频描述:").grid(row=2, column=0, sticky=tk.W, padx=5)
        self.desc_var = tk.StringVar(value="通过批量上传工具上传")
        ttk.Entry(settings_frame, textvariable=self.desc_var, width=50).grid(row=2, column=1, columnspan=3, sticky=(tk.W, tk.E), padx=5)
        
        # 3. 上传选项
        options_frame = ttk.LabelFrame(main_frame, text="上传选项", padding="5")
        options_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Label(options_frame, text="并发线程数:").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.threads_var = tk.StringVar(value="3")
        ttk.Spinbox(options_frame, from_=1, to=10, textvariable=self.threads_var, width=5).grid(row=0, column=1, sticky=tk.W, padx=5)
        
        ttk.Label(options_frame, text="最大重试次数:").grid(row=0, column=2, sticky=tk.W, padx=5)
        self.retries_var = tk.StringVar(value="3")
        ttk.Spinbox(options_frame, from_=0, to=10, textvariable=self.retries_var, width=5).grid(row=0, column=3, sticky=tk.W, padx=5)
        
        # 4. 操作按钮
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=3, column=0, columnspan=3, pady=10)
        
        ttk.Button(button_frame, text="设置登录凭据", command=self.setup_credentials).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="扫描视频文件", command=self.scan_videos).pack(side=tk.LEFT, padx=5)
        self.upload_btn = ttk.Button(button_frame, text="开始上传", command=self.start_upload)
        self.upload_btn.pack(side=tk.LEFT, padx=5)
        self.stop_btn = ttk.Button(button_frame, text="停止上传", command=self.stop_upload, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        
        # 5. 进度条
        ttk.Label(main_frame, text="上传进度:").grid(row=4, column=0, sticky=tk.W, pady=5)
        self.progress = ttk.Progressbar(main_frame, mode='determinate')
        self.progress.grid(row=4, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        # 6. 日志输出
        ttk.Label(main_frame, text="日志输出:").grid(row=5, column=0, sticky=(tk.W, tk.N), pady=5)
        
        log_frame = ttk.Frame(main_frame)
        log_frame.grid(row=5, column=1, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=15, width=70)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 设置日志处理器
        self.setup_log_handler()
    
    def setup_log_handler(self):
        """设置日志处理器，将日志输出到GUI"""
        class GUILogHandler(logging.Handler):
            def __init__(self, text_widget):
                super().__init__()
                self.text_widget = text_widget
            
            def emit(self, record):
                msg = self.format(record)
                self.text_widget.insert(tk.END, msg + '\n')
                self.text_widget.see(tk.END)
                self.text_widget.update()
        
        # 创建GUI日志处理器
        gui_handler = GUILogHandler(self.log_text)
        gui_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        
        # 添加到uploader的logger
        self.uploader.logger.addHandler(gui_handler)
        self.uploader.logger.setLevel(logging.INFO)
    
    def browse_folder(self):
        """浏览文件夹"""
        folder = filedialog.askdirectory(title="选择视频文件夹")
        if folder:
            self.folder_var.set(folder)
    
    def setup_credentials(self):
        """设置登录凭据"""
        def on_submit():
            cookies = {}
            if sessdata_var.get():
                cookies['SESSDATA'] = sessdata_var.get()
            if bili_jct_var.get():
                cookies['bili_jct'] = bili_jct_var.get()
            if dedeuserid_var.get():
                cookies['DedeUserID'] = dedeuserid_var.get()
            if dedemd5_var.get():
                cookies['DedeUserID__ckMd5'] = dedemd5_var.get()
            
            if len(cookies) >= 2:
                self.uploader.config.cookies = cookies
                self.uploader.save_config()
                messagebox.showinfo("成功", "登录凭据设置成功！")
                cred_window.destroy()
            else:
                messagebox.showerror("错误", "请至少填写SESSDATA和bili_jct")
        
        # 创建凭据设置窗口
        cred_window = tk.Toplevel(self.root)
        cred_window.title("设置B站登录凭据")
        cred_window.geometry("400x300")
        cred_window.transient(self.root)
        cred_window.grab_set()
        
        # 凭据输入框
        ttk.Label(cred_window, text="请输入B站cookies信息:").pack(pady=10)
        
        frame = ttk.Frame(cred_window, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)
        
        # SESSDATA
        ttk.Label(frame, text="SESSDATA:").grid(row=0, column=0, sticky=tk.W, pady=5)
        sessdata_var = tk.StringVar(value=self.uploader.config.cookies.get('SESSDATA', ''))
        ttk.Entry(frame, textvariable=sessdata_var, width=50).grid(row=0, column=1, pady=5, padx=5)
        
        # bili_jct
        ttk.Label(frame, text="bili_jct:").grid(row=1, column=0, sticky=tk.W, pady=5)
        bili_jct_var = tk.StringVar(value=self.uploader.config.cookies.get('bili_jct', ''))
        ttk.Entry(frame, textvariable=bili_jct_var, width=50).grid(row=1, column=1, pady=5, padx=5)
        
        # DedeUserID
        ttk.Label(frame, text="DedeUserID:").grid(row=2, column=0, sticky=tk.W, pady=5)
        dedeuserid_var = tk.StringVar(value=self.uploader.config.cookies.get('DedeUserID', ''))
        ttk.Entry(frame, textvariable=dedeuserid_var, width=50).grid(row=2, column=1, pady=5, padx=5)
        
        # DedeUserID__ckMd5
        ttk.Label(frame, text="DedeUserID__ckMd5:").grid(row=3, column=0, sticky=tk.W, pady=5)
        dedemd5_var = tk.StringVar(value=self.uploader.config.cookies.get('DedeUserID__ckMd5', ''))
        ttk.Entry(frame, textvariable=dedemd5_var, width=50).grid(row=3, column=1, pady=5, padx=5)
        
        # 按钮
        btn_frame = ttk.Frame(cred_window)
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text="保存", command=on_submit).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="取消", command=cred_window.destroy).pack(side=tk.LEFT, padx=5)
    
    def scan_videos(self):
        """扫描视频文件"""
        folder = self.folder_var.get()
        if not folder:
            messagebox.showerror("错误", "请先选择视频文件夹")
            return
        
        try:
            # 清空日志
            self.log_text.delete(1.0, tk.END)
            
            # 扫描文件
            video_files = self.uploader.scan_video_files(folder)
            
            if video_files:
                messagebox.showinfo("扫描完成", f"共发现 {len(video_files)} 个视频文件")
            else:
                messagebox.showwarning("扫描完成", "未发现任何视频文件")
                
        except Exception as e:
            messagebox.showerror("扫描错误", f"扫描文件夹时出错: {e}")
    
    def start_upload(self):
        """开始上传"""
        folder = self.folder_var.get()
        if not folder:
            messagebox.showerror("错误", "请先选择视频文件夹")
            return
        
        if not self.uploader.config.cookies and not self.uploader.config.access_token:
            messagebox.showerror("错误", "请先设置B站登录凭据")
            return
        
        # 更新配置
        self.update_config()
        
        # 确认上传
        if not messagebox.askyesno("确认上传", "确定要开始批量上传视频吗？"):
            return
        
        # 开始上传
        self.is_uploading = True
        self.upload_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        
        # 清空日志和进度
        self.log_text.delete(1.0, tk.END)
        self.progress['value'] = 0
        
        # 在新线程中执行上传
        self.upload_thread = threading.Thread(target=self.upload_worker, args=(folder,))
        self.upload_thread.daemon = True
        self.upload_thread.start()
    
    def stop_upload(self):
        """停止上传"""
        self.is_uploading = False
        self.upload_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.uploader.logger.info("用户停止上传任务")
    
    def update_config(self):
        """更新配置"""
        # 版权类型
        self.uploader.config.copyright = 1 if self.copyright_var.get() == "自制" else 2
        
        # 分区
        try:
            self.uploader.config.tid = int(self.tid_var.get())
        except ValueError:
            self.uploader.config.tid = 171
        
        # 标签
        tags = [tag.strip() for tag in self.tags_var.get().split(',') if tag.strip()]
        self.uploader.config.tags = tags
        
        # 描述
        self.uploader.config.description = self.desc_var.get()
        
        # 线程数
        try:
            threads = int(self.threads_var.get())
            self.uploader.config.threads = max(1, min(10, threads))
        except ValueError:
            self.uploader.config.threads = 3
        
        # 重试次数
        try:
            retries = int(self.retries_var.get())
            self.uploader.config.max_retries = max(0, min(10, retries))
        except ValueError:
            self.uploader.config.max_retries = 3
    
    def upload_worker(self, folder_path):
        """上传工作线程"""
        try:
            # 扫描视频文件
            video_files = self.uploader.scan_video_files(folder_path)
            
            if not video_files:
                self.uploader.logger.warning("未发现任何视频文件，上传任务结束")
                return
            
            self.uploader.upload_stats["total"] = len(video_files)
            
            # 更新进度条最大值
            self.root.after(0, lambda: self.progress.config(maximum=len(video_files)))
            
            # 逐个上传
            for i, video_file in enumerate(video_files):
                if not self.is_uploading:
                    break
                
                self.uploader.logger.info(f"[{i+1}/{len(video_files)}] 正在处理: {video_file.filename}")
                
                # 上传文件
                retry_count = 0
                while retry_count <= self.uploader.config.max_retries and self.is_uploading:
                    if self.uploader.upload_single_video(video_file):
                        break
                    
                    retry_count += 1
                    if retry_count <= self.uploader.config.max_retries:
                        self.uploader.logger.info(f"第 {retry_count} 次重试: {video_file.filename}")
                        if self.is_uploading:
                            time.sleep(5)
                
                # 更新进度条
                self.root.after(0, lambda: self.progress.config(value=i+1))
            
            # 显示结果
            if self.is_uploading:
                self.uploader._show_upload_results(0)
                
        except Exception as e:
            self.uploader.logger.error(f"上传过程中出现错误: {e}")
        finally:
            # 恢复按钮状态
            self.root.after(0, self.upload_finished)
    
    def upload_finished(self):
        """上传完成回调"""
        self.is_uploading = False
        self.upload_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
    
    def run(self):
        """运行GUI"""
        self.root.mainloop()


def main():
    """主程序入口"""
    try:
        app = UploaderGUI()
        app.run()
    except Exception as e:
        print(f"GUI启动失败: {e}")
        print("请确保已安装tkinter库")


if __name__ == "__main__":
    main()