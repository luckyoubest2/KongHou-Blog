---
title: 在CherryStudio中配置虎鲸笔记MCP的方法
date: 2025-12-08T20:40:00+08:00
draft: false
tags:
 - CherryStudio
 - 虎鲸笔记
 - MCP
categories:
 - 解决方案
collections:
 - 笔记软件相关  
---






## 前言

虎鲸笔记是一款优秀的本地大纲式双链笔记软件，其本身提供了优秀的AI能力，并提供MCP服务。

Cherry Studio 是一款功能全面的 AI 助手平台，集成了多模型对话、AI 绘画、翻译和知识库管理等功能。它支持主流 AI 模型和本地部署，提供 300 多个预配置助手和高度自定义选项。该平台兼容多操作系统，注重数据安全，并提供个性化设置和快捷功能。是一个全面的AI工具。

本文旨在简要说明如何将虎鲸笔记的MCP服务接入Cherry Studio，并优化使用体验。

<!--more-->

## 准备工作

本文基于的各软件版本为：

- 虎鲸笔记：v1.54.0（2025年12月5日）
- CherryStudio：v1.7.1（2025年12月1日）

## 步骤

### 1. 在虎鲸笔记中配置密钥

打开虎鲸笔记，点击 ``虎鲸笔记 - 设置 - AI助手`` ，在``MCP服务器Token``文本框中配置密钥

> [!CAUTION]
>
> 不要加入 ``Bearer``表头，保持英文符号

![image-20251208104721983](https://cdn.jsdelivr.net/gh/luckyoubest2/Bolg-IMG/202512081137904.png)

### 2. 在Cherry Studio中配置MCP

#### 法1：通过导入JSON配置（推荐）

在Cherr Studio中点击`` 设置 - MCP - 添加 - 从JSON导入``，粘贴下列代码

```json
{
  "mcpServers": {
    "Orca-Note": {
      "name": "Orca Note",
      "type": "streamableHttp",
      "baseUrl": "http://localhost:18672/mcp",
      "headers": {
        "Authorization": "Bearer example-use"
      }
    }
  }
}
```

> [!IMPORTANT]
> 将步骤1中设置的Token替换代码中的``example-use``，与``Bearer``保持一个英文空格

> [!NOTE]
>
> ``Name``后可自行更改名称



#### 法2：通过快速创建配置

在Cherr Studio中点击`` 设置 - MCP - 添加 - 快速创建``，创建并做如下配置

![image-20251208105423405](https://cdn.jsdelivr.net/gh/luckyoubest2/Bolg-IMG/202512081137905.png)

需要用到的代码段：

```md
http://localhost:18672/mcp
```

```md
Authorization=Bearer example-use
```

> [!IMPORTANT]
>
> 将步骤1中设置的Token替换代码中的``example-use``，与``Bearer``保持一个英文空格

### 3. 检验

配置完成后能正确读取9个工具即为配置成功

![image-20251208111539956](https://cdn.jsdelivr.net/gh/luckyoubest2/Bolg-IMG/202512081137906.png)

## 优化

上述配置完成后，访问虎鲸笔记库前还需要每次提供库ID，可以使用 Cherry Studio 自带的记忆功能优化使用体验。

在 Cherry Studio 中点击``设置 - 全局记忆 - 添加记忆``，输入以下文本：

> 虎鲸笔记调用需要的repo ID为``你的库ID``

![image-20251208113022111](https://cdn.jsdelivr.net/gh/luckyoubest2/Bolg-IMG/202512081137907.png)

> [!NOTE]
>
> 库ID的获取方法：在虎鲸笔记中点击``库 - 选择对应库 - 更多 - 打开文件夹``；文件名部分即为库ID

## 测试效果

在 Cherry Studio 中的使用效果如下：

![image-20251208112904757](https://cdn.jsdelivr.net/gh/luckyoubest2/Bolg-IMG/202512081137909.png)

