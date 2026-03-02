# AI Agent 从0开始学习demo库

wx专栏: [春哥的AI Agent通关秘籍](https://mp.weixin.qq.com/mp/appmsgalbum?__biz=MzI0NTAyNDMxMg==&action=getalbum&album_id=4366020748964970507#wechat_redirect)

# 单篇目录

- [《01：什么是Agent开发》](https://mp.weixin.qq.com/s/F7O-hMFLmOnR7IWTvQSZ7g)
- [《02：搭建环境及语言选择》](https://mp.weixin.qq.com/s/uxRFTudd0g-NoCHz7LbtvA)
- [《03：格式化输出》](https://mp.weixin.qq.com/s/Oqs-8Ng6oE3CNoAezA8KbA)
- [《04：智能记账小秘书【实战篇】》](https://mp.weixin.qq.com/s/8rVOP2WhOZiAErz8WGTYfw)
- [《05：工具调用 Function Calling【知识与思路篇】》](https://mp.weixin.qq.com/s/J51DTm4rv3DX_7TNjEBxww)
- [《06：你的第一款AI思维范式ReAct》](https://mp.weixin.qq.com/s/iLoqTdBRjZmzWeyI2O7IuA)
- [《07：5分钟实现文件归类助手【实战】》](https://mp.weixin.qq.com/s/YR5LrqZJA5PUYM9d9CFdcA)
- [《08：从【向量】到【句向量】》](https://mp.weixin.qq.com/s/dIdGRs5RPom6tFlOCnWg-g)
- [《09：从【句向量】到RAG》](https://mp.weixin.qq.com/s/6KkoXd8H3aIc_5PXh73azA)
- [《10：本地RAG实战（上）》](https://mp.weixin.qq.com/s/laEKF1o9d9GqATGeBCavRA)
- [《11：本地RAG实战（中上）》](https://mp.weixin.qq.com/s/alpXPDLFVMV112C6g2_YQA)
- [《12：本地RAG实战（中下）向量化与落库》](https://mp.weixin.qq.com/s/coNC3QlxAp09hzUz3HT8Wg)
- [《13：本地RAG实战（下）实现查询》](https://mp.weixin.qq.com/s/coNC3QlxAp09hzUz3HT8Wg)
- [《14：记忆才是Agent开发的核心》](https://mp.weixin.qq.com/s/5PKDx3ywtpR93Wa_9Y_d4g)

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
