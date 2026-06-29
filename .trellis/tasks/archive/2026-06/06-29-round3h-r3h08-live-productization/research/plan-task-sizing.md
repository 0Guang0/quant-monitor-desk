# Plan Task Sizing — R3H-08

| 切片       | CP  | 风险 | 说明                |
| ---------- | --- | ---- | ------------------- |
| S08-BOOT   | S   | 低   | 矩阵 + RED          |
| S08-01 08C | L   | 中   | 8 源 port           |
| S08-02 08A | M   | 中   | 3 CN 源             |
| S08-03 08B | L   | 中   | 10 validation 源    |
| S08-04 08D | S   | 低   | 2 概率源            |
| S08-05     | M   | 中   | reconcile/probe/CLI |
| S08-CLOSE  | S   | 低   | registry            |

**建议 PR：** S08-01 单独 PR；其余可合并（同 Wave 2 文件组）
