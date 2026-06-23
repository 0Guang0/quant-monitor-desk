"""SQL 标识符安全引用（quote_ident）测试。"""

from __future__ import annotations

import pytest
from backend.app.db.sql_identifiers import quote_ident


def test_quoteIdent_validName_returnsQuoted() -> None:
    """覆盖范围：合法小写表名引用
    测试对象：quote_ident
    目的/目标：常规 snake_case 标识符应被双引号包裹后原样保留
    验证点：quote_ident('file_registry') == '"file_registry"'
    失败含义：合法表名无法安全拼接进 SQL，动态 DDL/DML 会断
    """
    assert quote_ident("file_registry") == '"file_registry"'


def test_quoteIdent_withUnderscore_returnsQuoted() -> None:
    """覆盖范围：含下划线的长标识符引用
    测试对象：quote_ident
    目的/目标：多段下划线命名同样按契约加引号
    验证点：quote_ident('stg_foundation_smoke') == '"stg_foundation_smoke"'
    失败含义：staging 表名引用失败，迁移或写入 SQL 拼装出错
    """
    assert quote_ident("stg_foundation_smoke") == '"stg_foundation_smoke"'


def test_quoteIdent_injectionAttempt_raises() -> None:
    """覆盖范围：SQL 注入式标识符拒绝
    测试对象：quote_ident 对含分号/注释的输入
    目的/目标：禁止把多语句或注释塞进「标识符」参数
    验证点：注入字符串触发 ValueError，消息含 invalid SQL identifier
    失败含义：标识符未校验，动态 SQL 存在注入面
    """
    with pytest.raises(ValueError, match="invalid SQL identifier"):
        quote_ident("file_registry; DROP TABLE write_audit_log; --")


def test_quoteIdent_uppercase_raises() -> None:
    """覆盖范围：非 snake_case 大小写拒绝
    测试对象：quote_ident 对驼峰/大写输入
    目的/目标：仅允许小写加下划线，避免 DuckDB 大小写歧义
    验证点：FileRegistry 触发 ValueError
    失败含义：非规范标识符被接受，跨环境表名行为不一致
    """
    with pytest.raises(ValueError, match="invalid SQL identifier"):
        quote_ident("FileRegistry")


def test_quoteIdent_empty_raises() -> None:
    """覆盖范围：空标识符拒绝
    测试对象：quote_ident('')
    目的/目标：空串不是合法 SQL 标识符
    验证点：空输入触发 ValueError
    失败含义：空标识符可进入 SQL，生成语法错误或意外对象名
    """
    with pytest.raises(ValueError, match="invalid SQL identifier"):
        quote_ident("")
