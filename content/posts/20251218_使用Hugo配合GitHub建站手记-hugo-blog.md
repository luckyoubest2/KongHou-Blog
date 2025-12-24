---
title: 使用Hugo配合GitHub建站手记
date: 2025-12-18T12:50:00+08:00
draft: false
tags:
  - Hugo
  - GitHub
categories:
  - 解决方案
collections:
  - 建站笔记
---


## 前言

最近写了一些文章想着把文章发布了，在B站上搜索了一下尝试使用Hugo配合GitHub建站，总体来说还是十分方便的。

本次建站主要的参考资料有

- [FixIt - Hugo 主题](https://fixit.lruihao.cn/zh-cn/)

- [Hugo官方文档中文版|Hugo中文文档 | Hugo官方文档](https://hugo.opendocs.io/)

- [【Hugo】Hugo &#43; Github 免费部署自己的博客](https://letere-gzj.github.io/hugo-stack/p/hugo/custom-blog/)

## 一、准备工作

### 1. 安装Git

现代电脑一般都安装有Git，使用下列代码查询Git版本或者点击[链接](https://git-scm.com/book/zh/v2/%e8%b5%b7%e6%ad%a5-%e5%ae%89%e8%a3%85-Git)前往下载。

```Git
git --version
```

### 2. 安装Hugo

访问[Hugo官方文档](https://hugo.opendocs.io/installation/)获取更多帮助

#### 在MacOS上安装

推荐使用[Homebrew](https://brew.sh/zh-cn/)包管理器安装hugo，使用以下命令

```Go
brew install hugo
```

#### 在Windows上安装

访问[GitHub发布页面](https://github.com/gohugoio/hugo/releases/latest)下载形如`hugo_extended_withdeploy_0.152.2_windows-amd64.zip`的最新版本即可

解压缩后将hugo放入对应文件夹即可生效。

## 二、本地搭建博客

### 1. 创建博客

在目标文件夹，打开终端，输入以下命令

```Go
hugo new site my-blog
cd my-blog
hugo server -D
```

完成后访问`http://localhost:1313/`出现以下界面，则说明建站成功

![](https://cdn.jsdelivr.net/gh/luckyoubest2/Bolg-IMG/202512181250844.png)

![](https://cdn.jsdelivr.net/gh/luckyoubest2/Bolg-IMG/202512181250845.png)

### 2. 安装主题

本次建站使用「FixIt」主题，主题说明网站在此：[FixIt - Hugo 主题](https://fixit.lruihao.cn/zh-cn/)

#### ~~（0）官方建议~~

网站官方建议用以下命令一次性创建并使用主题，但是国内访问GitHub有些慢，建议直接下载

```Go
hugo new site my-blog
cd my-blog
git init
git submodule add https://github.com/hugo-fixit/FixIt.git themes/FixIt
echo "theme = 'FixIt'" >> hugo.toml
echo "defaultContentLanguage = 'zh-cn'" >> hugo.toml
hugo server
```

#### （1）安装主题

官方推荐的主题安装方式比较慢，建议直接前往[发布页面](https://github.com/hugo-fixit/FixIt/releases)下载最新主题。

1. 下载完成后解压并放置在`/themes`文件夹下，去除文件夹尾部的版本号标记。
   ![](https://cdn.jsdelivr.net/gh/luckyoubest2/Bolg-IMG/202512181250846.png)

1. 在网站根目录执行以下命令，并再次检查网页

   ```Go
   git init
   git submodule add https://github.com/hugo-fixit/FixIt.git themes/FixIt
echo "theme = 'FixIt'" >> hugo.toml
echo "defaultContentLanguage = 'zh-cn'" >> hugo.toml
   hugo server
   ```

   ![](https://cdn.jsdelivr.net/gh/luckyoubest2/Bolg-IMG/202512181250847.png)
   出现如图所示的网页则表示主题安装正确

### 3. 推送文章

1. 运行以下命令，创建文章

   ```Go
   hugo new content posts/my-first-post.md
   ```

1. 填写文章内容，重启服务器即可看到
   ![](https://cdn.jsdelivr.net/gh/luckyoubest2/Bolg-IMG/202512181250848.png)

1. 后续只要在`posts`文件夹下添加md文件即可生成文章

### 4. 配置网页

1. 在`FixIt`文件夹中找到`hugo.toml`文件，复制并替换根目录下的同名文件
   ![](https://cdn.jsdelivr.net/gh/luckyoubest2/Bolg-IMG/202512181250849.png)

1. 打开`hugo.toml`文件去除第18行的前面的`# `记号

   ```Go
   # theme list
   - # theme = ["FixIt"] # enable in your site config file
   + theme = ["FixIt"] # enable in your site config file
   ```

1. 再次回到网页，显示如下界面即表示配置成功
   ![](https://cdn.jsdelivr.net/gh/luckyoubest2/Bolg-IMG/202512181250850.png)

1. 具体参数请参考[配置 FixIt](https://fixit.lruihao.cn/zh-cn/documentation/getting-started/configuration/)

## 三、部署到GitHub

本文将采用GitHub Desktop直接部署，因此有些许不同。

### 1. 添加.gitignore文件

根目录创建`.gitignore`文件，并添加如下代码，以减小上传体积

```Go
# 自动生成的文件
public
resources
.hugo_build.lock

# hugo命令
hugo.exe
```

### 2. 创建Workflow文件

在根目录创建`.github/workflows/hugo.yaml`文件，并输入以下代码

```Go
# 用于构建和部署Hugo网站到GitHub Pages的示例工作流程
name: 发布Hugo网站到Pages

on:
  # 在目标为默认分支的推送上运行
  push:
    branches:
      - main

  # 允许您手动从“Actions”标签运行此工作流程
  workflow_dispatch:

# 设置GITHUB_TOKEN的权限，以允许部署到GitHub Pages
permissions:
  contents: read
  pages: write
  id-token: write

# 仅允许一个并发部署，跳过在进行中的运行与最新排队的运行之间排队的运行。
# 但是，请不要取消进行中的运行，因为我们希望这些生产部署能够完成。
concurrency:
  group: "pages"
  cancel-in-progress: false

# 默认使用bash
defaults:
  run:
    shell: bash

jobs:
  # 构建作业
  build:
    runs-on: ubuntu-latest
    env:
      HUGO_VERSION: 0.152.2
    steps:
      - name: 安装Hugo CLI
        run: |
          wget -O ${{ runner.temp }}/hugo.deb https://github.com/gohugoio/hugo/releases/download/v${HUGO_VERSION}/hugo_extended_${HUGO_VERSION}_linux-amd64.deb \
          && sudo dpkg -i ${{ runner.temp }}/hugo.deb          
      - name: 安装Dart Sass
        run: sudo snap install dart-sass
      - name: 检出
        uses: actions/checkout@v4
        with:
          submodules: recursive
          fetch-depth: 0
      - name: 设置Pages
        id: pages
        uses: actions/configure-pages@v3
      - name: 安装Node.js依赖
        run: "[[ -f package-lock.json || -f npm-shrinkwrap.json ]] && npm ci || true"
      - name: 使用Hugo构建
        env:
          # 为了与Hugo模块的最大向后兼容性
          HUGO_ENVIRONMENT: production
          HUGO_ENV: production
        run: |
          hugo \
            --gc \
            --minify \
            --baseURL "${{ steps.pages.outputs.base_url }}/"          
      - name: 上传构建产物
        uses: actions/upload-pages-artifact@v4
        with:
          path: ./public

  # 部署作业
  deploy:
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    runs-on: ubuntu-latest
    needs: build
    steps:
      - name: 部署到GitHub Pages
        id: deployment
        uses: actions/deploy-pages@v4
```



### 3. 将库发布到GitHub

1. 使用GitHub Desktop添加当前库
   ![](https://cdn.jsdelivr.net/gh/luckyoubest2/Bolg-IMG/202512181250851.png)

1. 发布并转为公开库
   ![](https://cdn.jsdelivr.net/gh/luckyoubest2/Bolg-IMG/202512181250852.png)

1. 访问GitHub在Action界面点击对应工作流，点击蓝色链接即可访问
   ![](https://cdn.jsdelivr.net/gh/luckyoubest2/Bolg-IMG/202512181250853.png)

## 四、一些美化

[Fixit-主题美化记录 | 毕少侠](https://geekswg.js.cool/posts/2023/fixit-beautification/)

[Fixit-主题美化 - 字节飞鸿](https://benelin.site/posts/hugo-fixit/a9f08a3/)
