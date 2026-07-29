# 5 套马卡龙色系锚（每首诗自动选一套·森哥拍板）

**每首诗根据意境自动选一套色系**（不是统一蓝）。每张生图 prompt 必须在头部嵌入对应色系的色彩词 + "macaron tones"。

---

## 1. 静谧月夜（薄荷蓝 + 月光银）
- **适用**：夜晚、静思、月亮、思乡
- **背景渐变**：`linear-gradient(135deg, #b8e0ff 0%, #fff3a0 50%, #ffd6e8 100%)`
- **生图 prompt 前缀**：
```
Children's watercolor picture book illustration,
soft pastel mint blue and moonlight silver color palette, macaron tones,
rounded shapes, simple and warm, no text, white background.
```
- **示例诗**：静夜思、望洞庭

## 2. 春日花朵（樱粉 + 鹅黄）
- **适用**：春天、鲜花、鸟鸣、嫩柳
- **背景渐变**：`linear-gradient(135deg, #ffd6e8 0%, #fff3a0 50%, #c8a8ff 100%)`
- **生图 prompt 前缀**：
```
Children's watercolor picture book illustration,
soft pastel cherry pink and cream yellow color palette, macaron tones,
spring blossom mood, rounded shapes, simple and warm, no text, white background.
```
- **示例诗**：望天门山、咏柳

## 3. 夏日明媚（天蓝 + 阳光黄）
- **适用**：夏天、阳光、儿童戏水、荷塘
- **背景渐变**：`linear-gradient(135deg, #b8e0ff 0%, #ffe066 50%, #6bdbb8 100%)`
- **生图 prompt 前缀**：
```
Children's watercolor picture book illustration,
soft pastel sky blue and sunshine yellow color palette, macaron tones,
bright summer mood, rounded shapes, simple and warm, no text, white background.
```
- **示例诗**：小池、所见、池上

## 4. 秋日暖阳（暖橙 + 奶油金）
- **适用**：秋天、落叶、思乡、丰收
- **背景渐变**：`linear-gradient(135deg, #ffe066 0%, #ff9eb5 50%, #c8a8ff 100%)`
- **生图 prompt 前缀**：
```
Children's watercolor picture book illustration,
soft pastel warm orange and golden cream color palette, macaron tones,
autumn warmth, rounded shapes, simple and warm, no text, white background.
```
- **示例诗**：登鹳雀楼、山行、枫桥夜泊

## 5. 冬日白雪（雪白 + 淡紫）
- **适用**：冬天、雪、寒梅、寒冷
- **背景渐变**：`linear-gradient(135deg, #e0eaff 0%, #f0e6ff 50%, #d6f0ff 100%)`
- **生图 prompt 前缀**：
```
Children's watercolor picture book illustration,
soft pastel snow white and icy lavender color palette, macaron tones,
gentle winter mood, rounded shapes, simple and warm, no text, white background.
```
- **示例诗**：江雪、千山鸟飞绝、梅

---

## 选 palette 的判断流程（deploy.py 自动决策）

1. 看诗题（出现"夜/月/思"→ 静谧月夜）
2. 看季节关键词（春→春日花朵，夏→夏日明媚，秋→秋日暖阳，冬→冬日白雪）
3. 看意境词（鸟/花/暖→春日花朵，雪/梅/寒→冬日白雪）
4. 不确定时 fallback 静谧月夜（最通用）

**不准问用户**（森哥硬偏好"澄清节流大任务最多 1 个澄清"）。deploy.py 自动判断，直接选默认最匹配的。