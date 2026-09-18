# Elena_Fu的内容运营作品集

展示账号运营、老师 IP、官号拟人厚厚、官方 IP 过儿、图文视频创作、AI 短剧及产品推广案例。

这是为 GitHub Pages 整理的静态网站项目，使用 HTML、CSS 和 JavaScript，无需数据库。

- GitHub 仓库：[elena0401bb/elenafbb](https://github.com/elena0401bb/elenafbb)
- 网站地址：https://elena0401bb.github.io/elenafbb/

公开署名统一使用 **Elena_Fu**，页面不公开联系邮箱。发布检查会阻止邮箱或邮件链接进入网站。

## 文件

- `site/index.html`：网站首页。
- `site/`：八个页面及其引用的图片、样式和交互文件。
- `tools/sync_from_workspace.py`：从当前工作目录导出最新网页及所需素材。
- `tools/check_site.py`：检查图片、样式、页面链接和区块定位。
- `tools/optimize_images.py`：发布时生成多尺寸 WebP 预览图，按屏幕大小加载，原图保留供放大查看。
- `.github/workflows/pages.yml`：更新推送到 `main` 后，检查并发布网站。

## 本地修改与同步

目前继续在原作品集工作目录中修改和核对文案。完成一批修改后，运行以下命令，刷新本项目中的发布文件：

```sh
python3 tools/sync_from_workspace.py
```

导出需要 Python 3.10 或以上版本及 Pillow（`python3 -m pip install Pillow`）。导出时自动生成 480、800、1280 像素宽的预览图，不放大小尺寸原图；首屏优先加载，后续图片延迟加载。预览图文件名包含内容指纹，后续发布会复用未变更的图片。原始素材与放大查看链接保留。

其他使用者可直接编辑 `site/`，不需要导出工具。`index.html` 与 `portfolio-yangcong-draft.html` 是同一首页的两个入口，使用导出工具时会同时更新。`site/_images/` 是自动生成的预览目录，请勿在其中手工存放素材。

本机已通过 GitHub Desktop 连接这个仓库。每次完成一批修改，先导出、检查并生成提交：

```sh
python3 tools/publish.py --prepare-only --message "更新作品集文案与展示"
```

然后在 GitHub Desktop 中选择本仓库，点击 **Push origin**。在 Codex 中协作时，可由助手完成上述步骤；在本机另行配置命令行认证后，也可省略 `--prepare-only` 直接上传。

GitHub Pages 工作流会在上传后更新网站。**本地保存文件本身不会触发远程更新**；发布步骤以一轮修改完成为单位。当前未安装后台监听或定时上传。单独运行 `python3 tools/check_site.py` 可检查发布文件的本地链接。

## 首次发布

1. 在选定的 GitHub 账号下创建作品集仓库，将本目录作为仓库根目录。
2. 在仓库的 Settings → Pages 中选择 GitHub Actions 作为发布来源。
3. 将准备公开的版本推送到 `main`，等待 Publish portfolio 工作流成功。
4. 使用工作流返回的 GitHub Pages 地址访问网站。

项目站点的网址形式为 `https://用户名.github.io/仓库名/`。公开仓库可使用 GitHub Free 的 Pages 服务。

## 代码与作品素材

网页实现代码采用 MIT 许可证；个人案例文案、图片、品牌标识及第三方素材不在该许可范围内。详见 [LICENSE](LICENSE) 和 [作品内容与素材说明](CONTENT_NOTICE.md)。

## 官方文档

- [GitHub Pages 简介](https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages)
- [用 GitHub Actions 发布 Pages](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages)
- [仓库许可证](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/licensing-a-repository)
