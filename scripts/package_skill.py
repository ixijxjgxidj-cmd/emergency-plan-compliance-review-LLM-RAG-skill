#!/usr/bin/env python3
"""打包本 Skill 为可上传的 zip，并校验 SKILL.md 位于压缩包根目录。

用法：
    python scripts/package_skill.py            # 生成 dist/emergency-plan-compliance-review.zip
    python scripts/package_skill.py --check    # 只做结构校验，不打包
    python scripts/package_skill.py --with-samples  # 同时打包 laws/ 与 plan/ 中的示例文件

设计要点：
- zip 内**根目录直接是 SKILL.md**，不套任何中间目录。这是"上传后提示未找到 SKILL.md"的
  唯一常见原因，因此打包后会强制自检。
- 默认不打包 laws/、plan/、output/ 中的用户资料（可能含未公开文件），只保留 .gitkeep 占位。
"""

from __future__ import annotations

import argparse
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PKG_NAME = "emergency-plan-compliance-review"

# 必须存在的入口与结构
REQUIRED_FILES = [
    "SKILL.md",
    "AGENTS.md",
    "CLAUDE.md",
    "README.md",
    "prompts/master.md",
    "prompts/model_config_template.json",
    "references/plan_type_matrix.md",
    "references/issue_types.md",
]

REQUIRED_PROMPTS = [
    "00_plan_profiling",
    "01_law_inventory",
    "02_law_classification",
    "03_kb_build",
    "04_clause_split",
    "05A_rule_screening",
    "05B_llm_deep_review",
    "05C_cross_audit",
    "05C2_fulltext_crosscheck",
    "05D_recheck",
    "05E_final_audit",
    "06_missing_basis_review",
    "07_web_verification",
    "08_result_summary",
]

# 必须保留的空目录占位
KEEP_DIRS = ["laws", "plan", "output"]

EXCLUDE_DIR_NAMES = {
    "__pycache__", ".git", ".pytest_cache", ".mypy_cache",
    ".ruff_cache", "dist", "chroma_db", ".vscode", ".idea",
}
EXCLUDE_SUFFIXES = {".pyc", ".pyo", ".zip"}
# 默认不入包的用户资料目录
SAMPLE_DIRS = {"laws", "plan", "output"}


def check_structure() -> list[str]:
    errors: list[str] = []

    for rel in REQUIRED_FILES:
        if not (ROOT / rel).is_file():
            errors.append(f"缺少必需文件：{rel}")

    for stage in REQUIRED_PROMPTS:
        p = ROOT / "prompts" / stage / "prompt.md"
        if not p.is_file():
            errors.append(f"缺少阶段 prompt：prompts/{stage}/prompt.md")

    # SKILL.md 必须有 frontmatter 的 name 与 description
    skill = ROOT / "SKILL.md"
    if skill.is_file():
        text = skill.read_text(encoding="utf-8")
        if not text.startswith("---"):
            errors.append("SKILL.md 缺少 YAML frontmatter（必须以 --- 开头）")
        else:
            fm = text.split("---", 2)[1]
            for key in ("name:", "description:"):
                if key not in fm:
                    errors.append(f"SKILL.md frontmatter 缺少 {key}")

    # 不允许出现嵌套的 skills/<name>/SKILL.md，这会导致上传后识别失败
    for nested in ROOT.rglob("SKILL.md"):
        if nested != skill:
            errors.append(f"发现多余的嵌套 SKILL.md：{nested.relative_to(ROOT)}（请删除，入口只能有一个）")

    for d in KEEP_DIRS:
        keep = ROOT / d / ".gitkeep"
        if not keep.is_file():
            errors.append(f"缺少目录占位：{d}/.gitkeep")

    return errors


def iter_files(with_samples: bool):
    for path in sorted(ROOT.rglob("*")):
        rel = path.relative_to(ROOT)
        parts = rel.parts

        if any(part in EXCLUDE_DIR_NAMES for part in parts):
            continue
        if path.is_dir():
            continue
        if path.suffix in EXCLUDE_SUFFIXES:
            continue
        if not with_samples and parts[0] in SAMPLE_DIRS and path.name != ".gitkeep":
            continue
        yield path, rel


def build(with_samples: bool) -> Path:
    dist = ROOT / "dist"
    dist.mkdir(exist_ok=True)
    target = dist / f"{PKG_NAME}.zip"
    if target.exists():
        target.unlink()

    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as zf:
        for path, rel in iter_files(with_samples):
            zf.write(path, rel.as_posix())

    # 打包后自检：SKILL.md 必须在根目录
    with zipfile.ZipFile(target) as zf:
        names = zf.namelist()
    if "SKILL.md" not in names:
        target.unlink(missing_ok=True)
        raise SystemExit("打包失败：zip 根目录下没有 SKILL.md，已删除产物。")

    print(f"打包完成：{target.relative_to(ROOT)}")
    print(f"文件数：{len(names)}")
    print("根目录入口校验通过：SKILL.md 位于 zip 根目录。")
    return target


def main() -> int:
    ap = argparse.ArgumentParser(description="打包应急预案合规审查 Skill")
    ap.add_argument("--check", action="store_true", help="只校验结构，不打包")
    ap.add_argument("--with-samples", action="store_true",
                    help="同时打包 laws/、plan/ 中的示例文件（注意：可能含敏感资料）")
    args = ap.parse_args()

    errors = check_structure()
    if errors:
        print("结构校验未通过：", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        return 1
    print("结构校验通过。")

    if args.check:
        return 0

    build(args.with_samples)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
