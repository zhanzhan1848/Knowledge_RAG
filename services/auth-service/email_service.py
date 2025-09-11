#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
邮件服务模块

提供邮件发送功能，包括邮箱验证、密码重置等邮件模板。

作者: Knowledge RAG Team
创建时间: 2024
"""

import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from jinja2 import Template
import logging

from config import get_config

config = get_config()
logger = logging.getLogger(__name__)


class EmailService:
    """
    邮件服务类
    
    负责发送各种类型的邮件，包括验证邮件、密码重置邮件等。
    """
    
    def __init__(self):
        """
        初始化邮件服务
        """
        self.smtp_server = config.email_smtp_server
        self.smtp_port = config.email_smtp_port
        self.username = config.email_username
        self.password = config.email_password
        self.from_email = config.email_from
        self.use_tls = config.email_use_tls
    
    def _create_connection(self) -> smtplib.SMTP:
        """
        创建SMTP连接
        
        Returns:
            smtplib.SMTP: SMTP连接对象
            
        Raises:
            Exception: 连接失败时抛出异常
        """
        try:
            if self.use_tls:
                context = ssl.create_default_context()
                server = smtplib.SMTP(self.smtp_server, self.smtp_port)
                server.starttls(context=context)
            else:
                server = smtplib.SMTP_SSL(self.smtp_server, self.smtp_port)
            
            server.login(self.username, self.password)
            return server
        except Exception as e:
            logger.error(f"邮件服务器连接失败: {e}")
            raise
    
    def send_email(
        self, 
        to_email: str, 
        subject: str, 
        html_content: str, 
        text_content: Optional[str] = None
    ) -> bool:
        """
        发送邮件
        
        Args:
            to_email: 收件人邮箱
            subject: 邮件主题
            html_content: HTML内容
            text_content: 纯文本内容（可选）
            
        Returns:
            bool: 发送是否成功
        """
        try:
            # 创建邮件消息
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = self.from_email
            message["To"] = to_email
            
            # 添加纯文本内容
            if text_content:
                text_part = MIMEText(text_content, "plain", "utf-8")
                message.attach(text_part)
            
            # 添加HTML内容
            html_part = MIMEText(html_content, "html", "utf-8")
            message.attach(html_part)
            
            # 发送邮件
            with self._create_connection() as server:
                server.send_message(message)
            
            logger.info(f"邮件发送成功: {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"邮件发送失败: {to_email}, 错误: {e}")
            return False
    
    def send_verification_email(self, to_email: str, username: str, token: str) -> bool:
        """
        发送邮箱验证邮件
        
        Args:
            to_email: 收件人邮箱
            username: 用户名
            token: 验证令牌
            
        Returns:
            bool: 发送是否成功
        """
        verification_url = f"{config.app_frontend_url}/verify-email?token={token}"
        
        # HTML模板
        html_template = Template("""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>邮箱验证</title>
            <style>
                body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
                .container { max-width: 600px; margin: 0 auto; padding: 20px; }
                .header { background: #007bff; color: white; padding: 20px; text-align: center; }
                .content { padding: 20px; background: #f9f9f9; }
                .button { display: inline-block; padding: 12px 24px; background: #007bff; color: white; text-decoration: none; border-radius: 4px; }
                .footer { padding: 20px; text-align: center; color: #666; font-size: 12px; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Knowledge RAG 系统</h1>
                </div>
                <div class="content">
                    <h2>邮箱验证</h2>
                    <p>亲爱的 {{ username }}，</p>
                    <p>感谢您注册 Knowledge RAG 系统！请点击下面的按钮验证您的邮箱地址：</p>
                    <p style="text-align: center; margin: 30px 0;">
                        <a href="{{ verification_url }}" class="button">验证邮箱</a>
                    </p>
                    <p>如果按钮无法点击，请复制以下链接到浏览器地址栏：</p>
                    <p><a href="{{ verification_url }}">{{ verification_url }}</a></p>
                    <p>此验证链接将在24小时后过期。</p>
                    <p>如果您没有注册此账户，请忽略此邮件。</p>
                </div>
                <div class="footer">
                    <p>此邮件由系统自动发送，请勿回复。</p>
                    <p>&copy; 2024 Knowledge RAG Team. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """)
        
        # 纯文本模板
        text_template = Template("""
        Knowledge RAG 系统 - 邮箱验证
        
        亲爱的 {{ username }}，
        
        感谢您注册 Knowledge RAG 系统！请访问以下链接验证您的邮箱地址：
        
        {{ verification_url }}
        
        此验证链接将在24小时后过期。
        
        如果您没有注册此账户，请忽略此邮件。
        
        此邮件由系统自动发送，请勿回复。
        
        © 2024 Knowledge RAG Team. All rights reserved.
        """)
        
        html_content = html_template.render(
            username=username,
            verification_url=verification_url
        )
        
        text_content = text_template.render(
            username=username,
            verification_url=verification_url
        )
        
        return self.send_email(
            to_email=to_email,
            subject="Knowledge RAG - 邮箱验证",
            html_content=html_content,
            text_content=text_content
        )
    
    def send_password_reset_email(self, to_email: str, username: str, token: str) -> bool:
        """
        发送密码重置邮件
        
        Args:
            to_email: 收件人邮箱
            username: 用户名
            token: 重置令牌
            
        Returns:
            bool: 发送是否成功
        """
        reset_url = f"{config.app_frontend_url}/reset-password?token={token}"
        
        # HTML模板
        html_template = Template("""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>密码重置</title>
            <style>
                body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
                .container { max-width: 600px; margin: 0 auto; padding: 20px; }
                .header { background: #dc3545; color: white; padding: 20px; text-align: center; }
                .content { padding: 20px; background: #f9f9f9; }
                .button { display: inline-block; padding: 12px 24px; background: #dc3545; color: white; text-decoration: none; border-radius: 4px; }
                .footer { padding: 20px; text-align: center; color: #666; font-size: 12px; }
                .warning { background: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; border-radius: 4px; margin: 20px 0; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Knowledge RAG 系统</h1>
                </div>
                <div class="content">
                    <h2>密码重置</h2>
                    <p>亲爱的 {{ username }}，</p>
                    <p>我们收到了您的密码重置请求。请点击下面的按钮重置您的密码：</p>
                    <p style="text-align: center; margin: 30px 0;">
                        <a href="{{ reset_url }}" class="button">重置密码</a>
                    </p>
                    <p>如果按钮无法点击，请复制以下链接到浏览器地址栏：</p>
                    <p><a href="{{ reset_url }}">{{ reset_url }}</a></p>
                    <div class="warning">
                        <strong>安全提醒：</strong>
                        <ul>
                            <li>此重置链接将在1小时后过期</li>
                            <li>如果您没有请求密码重置，请忽略此邮件</li>
                            <li>为了您的账户安全，请不要将此链接分享给他人</li>
                        </ul>
                    </div>
                </div>
                <div class="footer">
                    <p>此邮件由系统自动发送，请勿回复。</p>
                    <p>&copy; 2024 Knowledge RAG Team. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """)
        
        # 纯文本模板
        text_template = Template("""
        Knowledge RAG 系统 - 密码重置
        
        亲爱的 {{ username }}，
        
        我们收到了您的密码重置请求。请访问以下链接重置您的密码：
        
        {{ reset_url }}
        
        安全提醒：
        - 此重置链接将在1小时后过期
        - 如果您没有请求密码重置，请忽略此邮件
        - 为了您的账户安全，请不要将此链接分享给他人
        
        此邮件由系统自动发送，请勿回复。
        
        © 2024 Knowledge RAG Team. All rights reserved.
        """)
        
        html_content = html_template.render(
            username=username,
            reset_url=reset_url
        )
        
        text_content = text_template.render(
            username=username,
            reset_url=reset_url
        )
        
        return self.send_email(
            to_email=to_email,
            subject="Knowledge RAG - 密码重置",
            html_content=html_content,
            text_content=text_content
        )
    
    def send_welcome_email(self, to_email: str, username: str) -> bool:
        """
        发送欢迎邮件
        
        Args:
            to_email: 收件人邮箱
            username: 用户名
            
        Returns:
            bool: 发送是否成功
        """
        # HTML模板
        html_template = Template("""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>欢迎加入</title>
            <style>
                body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
                .container { max-width: 600px; margin: 0 auto; padding: 20px; }
                .header { background: #28a745; color: white; padding: 20px; text-align: center; }
                .content { padding: 20px; background: #f9f9f9; }
                .button { display: inline-block; padding: 12px 24px; background: #28a745; color: white; text-decoration: none; border-radius: 4px; }
                .footer { padding: 20px; text-align: center; color: #666; font-size: 12px; }
                .feature { background: white; padding: 15px; margin: 10px 0; border-radius: 4px; border-left: 4px solid #28a745; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>欢迎加入 Knowledge RAG 系统！</h1>
                </div>
                <div class="content">
                    <h2>欢迎，{{ username }}！</h2>
                    <p>恭喜您成功注册并验证了 Knowledge RAG 系统账户！</p>
                    
                    <h3>系统功能介绍：</h3>
                    <div class="feature">
                        <h4>🔍 智能检索</h4>
                        <p>基于先进的RAG技术，提供精准的知识检索服务</p>
                    </div>
                    <div class="feature">
                        <h4>📚 知识管理</h4>
                        <p>高效的文档管理和知识库构建功能</p>
                    </div>
                    <div class="feature">
                        <h4>🤖 AI问答</h4>
                        <p>智能问答系统，快速获取所需信息</p>
                    </div>
                    
                    <p style="text-align: center; margin: 30px 0;">
                        <a href="{{ app_url }}" class="button">开始使用</a>
                    </p>
                    
                    <p>如果您在使用过程中遇到任何问题，请随时联系我们的技术支持团队。</p>
                </div>
                <div class="footer">
                    <p>此邮件由系统自动发送，请勿回复。</p>
                    <p>&copy; 2024 Knowledge RAG Team. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """)
        
        html_content = html_template.render(
            username=username,
            app_url=config.app_frontend_url
        )
        
        return self.send_email(
            to_email=to_email,
            subject="欢迎加入 Knowledge RAG 系统！",
            html_content=html_content
        )


# 全局邮件服务实例
email_service = EmailService()


# 便捷函数
async def send_verification_email(email: str, username: str, token: str) -> bool:
    """
    发送验证邮件（异步包装）
    
    Args:
        email: 用户邮箱
        username: 用户名
        token: 验证令牌
        
    Returns:
        bool: 发送是否成功
    """
    return email_service.send_verification_email(email, username, token)


async def send_password_reset_email(email: str, username: str, token: str) -> bool:
    """
    发送密码重置邮件（异步包装）
    
    Args:
        email: 用户邮箱
        username: 用户名
        token: 重置令牌
        
    Returns:
        bool: 发送是否成功
    """
    return email_service.send_password_reset_email(email, username, token)


async def send_welcome_email(email: str, username: str) -> bool:
    """
    发送欢迎邮件（异步包装）
    
    Args:
        email: 用户邮箱
        username: 用户名
        
    Returns:
        bool: 发送是否成功
    """
    return email_service.send_welcome_email(email, username)