"""Python 源代码 AST 解析器 — 用于白盒测试的代码结构提取

使用 Python 内置的 ast 模块解析源码，提取：
- 函数定义（名称、参数、参数类型提示）
- 分支结构（if/elif/else，含条件表达式文本）
- 循环结构（for/while）
- 异常处理（try/except/finally）
- 返回语句
- 关键赋值和条件（用于路径覆盖分析）
"""

import ast
import os
from typing import Optional, Any
from pydantic import BaseModel, Field


class Branch(BaseModel):
    """代码分支"""
    line: int = Field(description="行号")
    type: str = Field(description="类型: if, elif, else, for, while, except")
    condition: str = Field(default="", description="条件表达式源码")
    body_lines: str = Field(default="", description="分支体的行号范围")
    has_return: bool = Field(default=False, description="是否包含return语句")


class FunctionInfo(BaseModel):
    """函数信息"""
    name: str = Field(description="函数名")
    decorators: list[str] = Field(default_factory=list, description="装饰器列表")
    args: list[str] = Field(default_factory=list, description="参数列表")
    line_start: int = Field(default=0)
    line_end: int = Field(default=0)
    docstring: str = Field(default="")
    branches: list[Branch] = Field(default_factory=list, description="分支列表")
    paths: list[list[str]] = Field(default_factory=list, description="执行路径列表")
    calls: list[str] = Field(default_factory=list, description="调用的函数列表")
    returns: list[str] = Field(default_factory=list, description="返回语句列表")


class CodeStructure(BaseModel):
    """代码结构（整个文件的分析结果）"""
    file_path: str = Field(description="源文件路径")
    functions: list[FunctionInfo] = Field(default_factory=list, description="函数列表")
    imports: list[str] = Field(default_factory=list, description="导入列表")
    global_vars: list[str] = Field(default_factory=list, description="全局变量")
    total_lines: int = Field(default=0)
    complexity_score: int = Field(default=0, description="圈复杂度估计")


class CodeParser:
    """Python 源码结构分析器

    使用 AST 提取代码结构信息，供 LLM 进行白盒测试分析。
    """

    def parse_file(self, file_path: str) -> CodeStructure:
        """解析单个 Python 文件

        Args:
            file_path: Python 源文件路径

        Returns:
            CodeStructure 包含所有函数、分支、路径信息
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")

        with open(file_path, "r", encoding="utf-8") as f:
            source = f.read()

        return self.parse_source(source, file_path)

    def parse_source(self, source: str, file_path: str = "<string>") -> CodeStructure:
        """解析源代码字符串"""
        tree = ast.parse(source)
        total_lines = len(source.split("\n"))

        structure = CodeStructure(
            file_path=file_path,
            total_lines=total_lines
        )

        for node in ast.walk(tree):
            # 提取导入
            if isinstance(node, ast.Import):
                for alias in node.names:
                    structure.imports.append(f"import {alias.name}")
            elif isinstance(node, ast.ImportFrom):
                names = ", ".join(a.name for a in node.names)
                structure.imports.append(f"from {node.module} import {names}")

            # 提取全局变量赋值
            elif isinstance(node, ast.Assign):
                if isinstance(node.targets[0], ast.Name):
                    name = node.targets[0].id
                    if name.isupper():  # 常量
                        structure.global_vars.append(name)

            # 提取函数定义
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                func = self._extract_function(node, source)
                structure.functions.append(func)
                structure.complexity_score += len(func.branches) + 1

        return structure

    def _extract_function(self, node: ast.FunctionDef, source: str) -> FunctionInfo:
        """从AST节点提取函数信息"""
        func = FunctionInfo(
            name=node.name,
            decorators=[self._get_decorator_name(d) for d in node.decorator_list],
            args=[a.arg for a in node.args.args],
            line_start=node.lineno,
            line_end=node.end_lineno or node.lineno,
            docstring=ast.get_docstring(node) or ""
        )

        # 提取分支
        for child in ast.walk(node):
            self._collect_branches(child, func, source)

        # 推导路径（简化：从分支组合推导）
        func.paths = self._derive_paths(func)

        # 提取返回语句
        class ReturnCollector(ast.NodeVisitor):
            def __init__(self):
                self.returns = []

            def visit_Return(self, n):
                self.returns.append(ast.unparse(n.value) if n.value else "None")

        collector = ReturnCollector()
        collector.visit(node)
        func.returns = collector.returns

        # 提取函数调用
        class CallCollector(ast.NodeVisitor):
            def __init__(self):
                self.calls = []

            def visit_Call(self, n):
                if isinstance(n.func, ast.Name):
                    self.calls.append(n.func.id)
                elif isinstance(n.func, ast.Attribute):
                    self.calls.append(ast.unparse(n.func))

        call_collector = CallCollector()
        call_collector.visit(node)
        func.calls = list(set(call_collector.calls))

        return func

    def _collect_branches(self, node: ast.AST, func: FunctionInfo, source: str):
        """收集分支信息"""
        branch = None

        if isinstance(node, ast.If):
            branch = Branch(
                line=node.lineno,
                type="if",
                condition=ast.unparse(node.test),
                body_lines=f"{node.body[0].lineno}-{node.body[-1].end_lineno}" if node.body else ""
            )
        elif isinstance(node, ast.For):
            branch = Branch(
                line=node.lineno,
                type="for",
                condition=f"for {ast.unparse(node.target)} in {ast.unparse(node.iter)}"
            )
        elif isinstance(node, ast.While):
            branch = Branch(
                line=node.lineno,
                type="while",
                condition=ast.unparse(node.test)
            )
        elif isinstance(node, ast.ExceptHandler):
            exc_type = ast.unparse(node.type) if node.type else "all"
            branch = Branch(
                line=node.lineno,
                type="except",
                condition=f"except {exc_type}"
            )

        if branch:
            # 检查分支体内是否有return
            branch.has_return = self._has_return(node)
            func.branches.append(branch)

    def _has_return(self, node: ast.AST) -> bool:
        """检查AST子树中是否包含return语句"""
        for child in ast.walk(node):
            if isinstance(child, ast.Return):
                return True
        return False

    def _derive_paths(self, func: FunctionInfo) -> list[list[str]]:
        """从分支推导关键执行路径

        简化算法：将每个分支视为决策点，生成代表性路径。
        对于LLM白盒分析，这里提供基本路径结构即可。
        """
        paths = []

        if not func.branches:
            paths.append(["entry → body → return"])
            return paths

        # 为每个if分支生成两条路径：条件True和条件False
        if_branches = [b for b in func.branches if b.type == "if"]

        if if_branches:
            # True路径
            true_desc = [f"Line{b.line}: {b.condition} == True" for b in if_branches]
            paths.append(true_desc)
            # False路径
            false_desc = [f"Line{b.line}: {b.condition} == False" for b in if_branches]
            paths.append(false_desc)

        # 异常路径
        except_branches = [b for b in func.branches if b.type == "except"]
        for eb in except_branches:
            paths.append([f"Line{eb.line}: {eb.condition} triggers"])

        return paths

    def _get_decorator_name(self, decorator: ast.expr) -> str:
        """获取装饰器名称"""
        if isinstance(decorator, ast.Name):
            return f"@{decorator.id}"
        elif isinstance(decorator, ast.Attribute):
            return f"@{ast.unparse(decorator)}"
        elif isinstance(decorator, ast.Call):
            if isinstance(decorator.func, ast.Name):
                return f"@{decorator.func.id}(...)"
            elif isinstance(decorator.func, ast.Attribute):
                return f"@{ast.unparse(decorator.func)}(...)"
        return "@unknown"

    def to_context_for_llm(self, structure: CodeStructure) -> str:
        """将代码结构转为LLM可读的文本上下文"""
        lines = [
            f"## 源代码文件: {structure.file_path}",
            f"总行数: {structure.total_lines}",
            f"圈复杂度估计: {structure.complexity_score}",
            "",
            "### 导入模块",
        ]
        for imp in structure.imports[:15]:
            lines.append(f"  {imp}")

        lines.append("")
        lines.append("### 函数列表")

        for func in structure.functions:
            lines.append(f"\n#### {func.name}")
            lines.append(f"- 装饰器: {', '.join(func.decorators) if func.decorators else '无'}")
            lines.append(f"- 参数: {', '.join(func.args)}")
            lines.append(f"- 行号: {func.line_start}-{func.line_end}")
            if func.docstring:
                lines.append(f"- 文档: {func.docstring[:100]}")

            if func.branches:
                lines.append("- 分支/决策点:")
                for b in func.branches:
                    ret_mark = " [含return]" if b.has_return else ""
                    lines.append(f"  * Line {b.line} ({b.type}): `{b.condition}`{ret_mark}")

            if func.returns:
                lines.append(f"- 返回语句: {', '.join(func.returns[:10])}")

            if func.calls:
                lines.append(f"- 关键调用: {', '.join(func.calls[:10])}")

        return "\n".join(lines)
