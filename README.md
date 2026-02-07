# AI Agent 从0开始学习demo库

wx专栏: [春哥的AI Agent通关秘籍](https://mp.weixin.qq.com/mp/appmsgalbum?__biz=MzI0NTAyNDMxMg==&action=getalbum&album_id=4366020748964970507#wechat_redirect)

# 单篇目录

- [《01、什么是Agent开发》](https://mp.weixin.qq.com/s?__biz=MzI0NTAyNDMxMg==&mid=2468167068&idx=1&sn=c5a1d1aa6dd8ea76c20be629913d32b9&chksm=ffbd4ecbc8cac7ddde139fa9a91309e4ade8e8859ac96f98dfa4fee4b8ac25ea0cec79b4e201&scene=178&cur_album_id=4366020748964970507&search_click_id=#rd)
- [《02、搭建环境及语言选择》](https://mp.weixin.qq.com/s?__biz=MzI0NTAyNDMxMg==&mid=2468167079&idx=1&sn=058bb94446ac6ece665a46aba515b87f&chksm=ffbd4ef0c8cac7e6bc93b1c64597bcfeb6f2eb8d3ace3eb67683345ebd90458e1f6356974fdc&scene=178&cur_album_id=4366020748964970507&search_click_id=#rd)
- [《03、格式化输出》](https://mp.weixin.qq.com/s/Oqs-8Ng6oE3CNoAezA8KbA)
- [《04、智能记账小秘书【实战篇】》](https://mp.weixin.qq.com/s/8rVOP2WhOZiAErz8WGTYfw)
- [《05、工具调用 Function Calling【知识与思路篇】》](https://mp.weixin.qq.com/s/J51DTm4rv3DX_7TNjEBxww)
- [《06、你的第一款AI思维范式ReAct》](https://mp.weixin.qq.com/s/iLoqTdBRjZmzWeyI2O7IuA)

## 如何启动本工程？

1. 按照 [《02、搭建环境及语言选择》](https://mp.weixin.qq.com/s?__biz=MzI0NTAyNDMxMg==&mid=2468167079&idx=1&sn=058bb94446ac6ece665a46aba515b87f&chksm=ffbd4ef0c8cac7e6bc93b1c64597bcfeb6f2eb8d3ace3eb67683345ebd90458e1f6356974fdc&scene=178&cur_album_id=4366020748964970507&search_click_id=#rd) 的内容创建 `miniconda` 开发环境。
2. 创建 `.env` 文件，并按照以下格式输入环境变量：

```.env
DEEP_SEEK_API_KEY = sk-xxxxx
DEEP_SEEK_API_URL = https://api.deepseek.com
```

其中 `DEEP_SEEK_API_KEY` 是你申请的 `deepseek` 的api key。

1. 执行命令(例子是power shell)

```bash
python .\lesson_03\lesson_03_structure.py
```
