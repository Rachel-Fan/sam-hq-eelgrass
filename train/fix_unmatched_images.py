#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
修复数据集 image/index 文件名不匹配的问题：
- 目录结构：<root>/{train,valid,test}/{image,index}/<files>
- 目标：删除只存在于 image 或 index 单侧的“孤儿文件”

默认 dry-run（只报告不删除）。加 --delete 才会真正删除。
可选：
  --ignore-ext     # 只比较不带扩展名的“主名”（stem），适用于同名不同后缀的情况
  --ignore-case    # 名字比较不区分大小写（Windows/混合数据源常用）
  --splits         # 自定义需要处理的 split 列表，默认 train,valid,test
  --image-dir/--index-dir  # 子目录名可改，默认 image / index
  --log-file       # 把报告另存为文本
"""

import argparse
import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple

def build_key(name: str, ignore_ext: bool, ignore_case: bool) -> str:
    p = Path(name)
    key = p.stem if ignore_ext else p.name
    return key.lower() if ignore_case else key

def list_files(d: Path) -> List[Path]:
    if not d.exists() or not d.is_dir():
        return []
    # 只收集普通文件（排除目录、链接的目录等）
    return [p for p in d.iterdir() if p.is_file()]

def collect_keys_map(files: List[Path], ignore_ext: bool, ignore_case: bool) -> Dict[str, List[Path]]:
    m: Dict[str, List[Path]] = {}
    for f in files:
        k = build_key(f.name, ignore_ext, ignore_case)
        m.setdefault(k, []).append(f)
    return m

def compute_orphans(
    image_map: Dict[str, List[Path]],
    index_map: Dict[str, List[Path]]
) -> Tuple[List[Path], List[Path]]:
    image_keys = set(image_map.keys())
    index_keys = set(index_map.keys())

    only_in_image = image_keys - index_keys
    only_in_index = index_keys - image_keys

    orphan_image_files = [f for k in only_in_image for f in image_map.get(k, [])]
    orphan_index_files = [f for k in only_in_index for f in index_map.get(k, [])]
    return orphan_image_files, orphan_index_files

def human_relpath(p: Path, root: Path) -> str:
    try:
        return str(p.relative_to(root))
    except Exception:
        return str(p)

def delete_files(files: List[Path]) -> Tuple[int, List[str]]:
    deleted = 0
    errors: List[str] = []
    for f in files:
        try:
            f.unlink(missing_ok=True)
            deleted += 1
        except Exception as e:
            errors.append(f"{f}: {e}")
    return deleted, errors

def process_split(
    root: Path,
    split: str,
    image_dirname: str,
    index_dirname: str,
    ignore_ext: bool,
    ignore_case: bool,
    do_delete: bool
) -> Tuple[str, str]:
    split_root = root / split
    image_dir = split_root / image_dirname
    index_dir = split_root / index_dirname

    report_lines = []
    error_lines = []

    if not split_root.exists():
        report_lines.append(f"[{split}] ✖ split 目录不存在：{human_relpath(split_root, root)}")
        return "\n".join(report_lines), "\n".join(error_lines)

    if not image_dir.exists() or not index_dir.exists():
        report_lines.append(f"[{split}] ✖ 缺少子目录：需要 '{image_dirname}' 与 '{index_dirname}'")
        if not image_dir.exists():
            report_lines.append(f"    - 缺少：{human_relpath(image_dir, root)}")
        if not index_dir.exists():
            report_lines.append(f"    - 缺少：{human_relpath(index_dir, root)}")
        return "\n".join(report_lines), "\n".join(error_lines)

    image_files = list_files(image_dir)
    index_files = list_files(index_dir)

    image_map = collect_keys_map(image_files, ignore_ext, ignore_case)
    index_map = collect_keys_map(index_files, ignore_ext, ignore_case)

    orphan_img, orphan_idx = compute_orphans(image_map, index_map)

    report_lines.append(f"[{split}] ✔ 扫描完成：image={len(image_files)}，index={len(index_files)}")
    report_lines.append(f"    - 仅在 image 的孤儿文件：{len(orphan_img)}")
    for p in sorted(orphan_img)[:10]:
        report_lines.append(f"        * {human_relpath(p, root)}")
    if len(orphan_img) > 10:
        report_lines.append(f"        … 共 {len(orphan_img)} 个")

    report_lines.append(f"    - 仅在 index 的孤儿文件：{len(orphan_idx)}")
    for p in sorted(orphan_idx)[:10]:
        report_lines.append(f"        * {human_relpath(p, root)}")
    if len(orphan_idx) > 10:
        report_lines.append(f"        … 共 {len(orphan_idx)} 个")

    if do_delete:
        del_count_img, del_err_img = delete_files(orphan_img)
        del_count_idx, del_err_idx = delete_files(orphan_idx)

        report_lines.append(f"    - 删除 image 孤儿：{del_count_img}/{len(orphan_img)}")
        report_lines.append(f"    - 删除 index 孤儿：{del_count_idx}/{len(orphan_idx)}")

        if del_err_img or del_err_idx:
            error_lines.extend([f"[{split}] 删除失败（image）: {e}" for e in del_err_img])
            error_lines.extend([f"[{split}] 删除失败（index）: {e}" for e in del_err_idx])
    else:
        report_lines.append("    - 试运行（未删除）。使用 --delete 进行删除。")

    return "\n".join(report_lines), "\n".join(error_lines)

def main():
    parser = argparse.ArgumentParser(description="清理 image/index 文件名不匹配的孤儿文件")
    parser.add_argument("root", type=str, help="数据集根目录（包含 train/ valid/ test/）")
    parser.add_argument("--splits", nargs="+", default=["train", "valid", "test"], help="要处理的 split 列表")
    parser.add_argument("--image-dir", default="image", help="image 子目录名（默认 image）")
    parser.add_argument("--index-dir", default="index", help="index 子目录名（默认 index）")
    parser.add_argument("-D", "--delete", action="store_true", help="执行删除（默认仅报告）")
    parser.add_argument("--ignore-ext", action="store_true", help="比较时忽略扩展名（按 stem 匹配）")
    parser.add_argument("--ignore-case", action="store_true", help="比较时忽略大小写")
    parser.add_argument("--log-file", type=str, default=None, help="将报告输出到文件")
    args = parser.parse_args()

    root = Path(args.root).resolve()

    all_reports = []
    all_errors = []

    for split in args.splits:
        rep, err = process_split(
            root=root,
            split=split,
            image_dirname=args.image_dir,
            index_dirname=args.index_dir,
            ignore_ext=args.ignore_ext,
            ignore_case=args.ignore_case,
            do_delete=args.delete,
        )
        all_reports.append(rep)
        if err:
            all_errors.append(err)

    final_report = "\n".join(all_reports)
    print(final_report)

    if all_errors:
        sys.stderr.write("\n[错误汇总]\n")
        sys.stderr.write("\n".join(all_errors) + "\n")

    # 选择性写日志
    if args.log_file:
        try:
            Path(args.log_file).write_text(final_report + ("\n\n[错误汇总]\n" + "\n".join(all_errors) if all_errors else ""), encoding="utf-8")
            print(f"\n日志已写入：{args.log_file}")
        except Exception as e:
            sys.stderr.write(f"\n写日志失败：{e}\n")

if __name__ == "__main__":
    main()
