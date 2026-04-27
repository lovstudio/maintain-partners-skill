# Changelog

All notable changes to this skill are documented here.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) · Versioning: [SemVer](https://semver.org/)

## [0.2.0] - 2026-04-27

### Added

- 新增多 logo 等高对齐工作流（Op 5）：file-level 裁切 + 等高 wrap box + 深底统一反白滤镜
- SVG 源文件需先用 rsvg-convert 栅格化再 normalize，否则 viewBox padding 无法裁切
- 深底反白配方：filter: brightness(0) invert(1) opacity(0.88)；已是白色源文件用 .ps-logo-original 跳过反白
- 明确反模式：禁止用 per-logo magic-number CSS height 调整（不稳定、不可维护）
- frontmatter description 扩充触发短语：logo 不一样高 / logo 对齐 / logo 大小不一致 / logo 颜色不统一

