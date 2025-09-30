"""
ジャンクファイルクリーンアップスクリプト
"""
import os
import shutil
import glob
import logging
from pathlib import Path
from typing import List, Dict, Any
import time
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class JunkFileCleaner:
    """ジャンクファイルクリーンアップクラス"""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.cleanup_stats = {
            'files_deleted': 0,
            'directories_deleted': 0,
            'bytes_freed': 0,
            'cleanup_time': 0.0
        }
        
        # クリーンアップ対象パターン
        self.file_patterns = [
            '**/__pycache__/**',
            '**/*.pyc',
            '**/*.pyo',
            '**/*.pyd',
            '**/*.so',
            '**/*.egg-info/**',
            '**/.pytest_cache/**',
            '**/.coverage',
            '**/htmlcov/**',
            '**/.mypy_cache/**',
            '**/.tox/**',
            '**/venv/**',
            '**/.venv/**',
            '**/env/**',
            '**/.env.local',
            '**/.env.*.local',
            '**/node_modules/**',
            '**/.DS_Store',
            '**/Thumbs.db',
            '**/*.log',
            '**/*.tmp',
            '**/*.temp',
            '**/*.bak',
            '**/*.swp',
            '**/*.swo',
            '**/*~',
            '**/.vscode/settings.json',
            '**/.idea/**',
            '**/*.orig',
            '**/*.rej'
        ]
        
        # 保持するファイルパターン（削除しない）
        self.keep_patterns = [
            '**/requirements*.txt',
            '**/config*.json',
            '**/env.example',
            '**/env.production',
            '**/README.md',
            '**/LICENSE',
            '**/.gitignore',
            '**/Dockerfile',
            '**/docker-compose.yml',
            '**/manage.sh',
            '**/main.py',
            '**/alembic.ini'
        ]
        
        # ログファイルの保持期間（日数）
        self.log_retention_days = 7
        
    def should_keep_file(self, file_path: Path) -> bool:
        """ファイルを保持するかどうかの判定"""
        file_str = str(file_path)
        
        # 保持パターンにマッチするかチェック
        for pattern in self.keep_patterns:
            if file_path.match(pattern):
                return True
        
        # 重要な設定ファイルは保持
        important_files = [
            'config.json',
            'config_testnet.json',
            'requirements.txt',
            'requirements_production.txt',
            'requirements_light.txt',
            'requirements_minimal.txt',
            'env.example',
            'env.production',
            'main.py',
            'manage.sh',
            'README.md',
            'Dockerfile',
            'docker-compose.yml',
            'alembic.ini'
        ]
        
        if file_path.name in important_files:
            return True
        
        return False
    
    def should_delete_log_file(self, file_path: Path) -> bool:
        """ログファイルを削除するかどうかの判定"""
        if not file_path.name.endswith('.log'):
            return False
        
        try:
            # ファイルの作成日時を取得
            file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
            cutoff_time = datetime.now() - timedelta(days=self.log_retention_days)
            
            return file_time < cutoff_time
        except Exception:
            return False
    
    def find_junk_files(self) -> List[Path]:
        """ジャンクファイルを検索"""
        junk_files = []
        
        for pattern in self.file_patterns:
            try:
                matches = self.project_root.glob(pattern)
                for match in matches:
                    if match.is_file():
                        # 保持すべきファイルかチェック
                        if not self.should_keep_file(match):
                            # ログファイルの場合は期間チェック
                            if match.name.endswith('.log'):
                                if self.should_delete_log_file(match):
                                    junk_files.append(match)
                            else:
                                junk_files.append(match)
                    elif match.is_dir():
                        # ディレクトリの場合は内容をチェック
                        if self._is_empty_or_junk_directory(match):
                            junk_files.append(match)
                            
            except Exception as e:
                logger.warning(f"Error processing pattern {pattern}: {e}")
        
        return junk_files
    
    def _is_empty_or_junk_directory(self, dir_path: Path) -> bool:
        """ディレクトリが空またはジャンクかどうかの判定"""
        try:
            # __pycache__ディレクトリは常に削除対象
            if dir_path.name == '__pycache__':
                return True
            
            # 空のディレクトリは削除対象
            if not any(dir_path.iterdir()):
                return True
            
            # 特定のディレクトリ名は削除対象
            junk_dir_names = [
                '.pytest_cache',
                '.mypy_cache',
                '.tox',
                'node_modules',
                'htmlcov',
                '.coverage'
            ]
            
            if dir_path.name in junk_dir_names:
                return True
            
            return False
            
        except Exception:
            return False
    
    def cleanup_junk_files(self, dry_run: bool = True) -> Dict[str, Any]:
        """ジャンクファイルのクリーンアップ"""
        start_time = time.time()
        
        logger.info(f"Starting junk file cleanup (dry_run={dry_run})")
        
        # ジャンクファイル検索
        junk_files = self.find_junk_files()
        
        logger.info(f"Found {len(junk_files)} junk files/directories")
        
        deleted_files = []
        deleted_dirs = []
        bytes_freed = 0
        
        for item in junk_files:
            try:
                if item.is_file():
                    file_size = item.stat().st_size
                    
                    if not dry_run:
                        item.unlink()
                        bytes_freed += file_size
                        self.cleanup_stats['files_deleted'] += 1
                    
                    deleted_files.append({
                        'path': str(item),
                        'size': file_size,
                        'type': 'file'
                    })
                    
                elif item.is_dir():
                    dir_size = self._get_directory_size(item)
                    
                    if not dry_run:
                        shutil.rmtree(item)
                        bytes_freed += dir_size
                        self.cleanup_stats['directories_deleted'] += 1
                    
                    deleted_dirs.append({
                        'path': str(item),
                        'size': dir_size,
                        'type': 'directory'
                    })
                
                logger.info(f"{'Would delete' if dry_run else 'Deleted'}: {item}")
                
            except Exception as e:
                logger.error(f"Failed to delete {item}: {e}")
        
        # 統計更新
        self.cleanup_stats['bytes_freed'] = bytes_freed
        self.cleanup_stats['cleanup_time'] = time.time() - start_time
        
        return {
            'deleted_files': deleted_files,
            'deleted_directories': deleted_dirs,
            'total_items': len(junk_files),
            'bytes_freed': bytes_freed,
            'cleanup_time': self.cleanup_stats['cleanup_time'],
            'dry_run': dry_run
        }
    
    def _get_directory_size(self, dir_path: Path) -> int:
        """ディレクトリのサイズ計算"""
        total_size = 0
        try:
            for file_path in dir_path.rglob('*'):
                if file_path.is_file():
                    total_size += file_path.stat().st_size
        except Exception:
            pass
        return total_size
    
    def format_bytes(self, bytes_value: int) -> str:
        """バイト数を人間が読みやすい形式に変換"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes_value < 1024.0:
                return f"{bytes_value:.1f} {unit}"
            bytes_value /= 1024.0
        return f"{bytes_value:.1f} TB"
    
    def generate_cleanup_report(self, cleanup_result: Dict[str, Any]) -> str:
        """クリーンアップレポート生成"""
        report = []
        report.append("=" * 60)
        report.append("JUNK FILE CLEANUP REPORT")
        report.append("=" * 60)
        report.append(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Mode: {'DRY RUN' if cleanup_result['dry_run'] else 'ACTUAL CLEANUP'}")
        report.append("")
        
        report.append("SUMMARY:")
        report.append(f"  Total items processed: {cleanup_result['total_items']}")
        report.append(f"  Files: {len(cleanup_result['deleted_files'])}")
        report.append(f"  Directories: {len(cleanup_result['deleted_directories'])}")
        report.append(f"  Space freed: {self.format_bytes(cleanup_result['bytes_freed'])}")
        report.append(f"  Cleanup time: {cleanup_result['cleanup_time']:.2f} seconds")
        report.append("")
        
        if cleanup_result['deleted_files']:
            report.append("DELETED FILES:")
            for item in cleanup_result['deleted_files'][:10]:  # 最初の10件のみ表示
                report.append(f"  {item['path']} ({self.format_bytes(item['size'])})")
            
            if len(cleanup_result['deleted_files']) > 10:
                report.append(f"  ... and {len(cleanup_result['deleted_files']) - 10} more files")
            report.append("")
        
        if cleanup_result['deleted_directories']:
            report.append("DELETED DIRECTORIES:")
            for item in cleanup_result['deleted_directories']:
                report.append(f"  {item['path']} ({self.format_bytes(item['size'])})")
            report.append("")
        
        report.append("=" * 60)
        
        return "\n".join(report)

def main():
    """メイン関数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Junk File Cleanup Tool')
    parser.add_argument('--project-root', default='.', help='Project root directory')
    parser.add_argument('--dry-run', action='store_true', default=True, help='Dry run mode')
    parser.add_argument('--execute', action='store_true', help='Actually delete files')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    # ログ設定
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # クリーンアップ実行
    cleaner = JunkFileCleaner(args.project_root)
    
    # 実行モード決定
    dry_run = not args.execute
    
    try:
        result = cleaner.cleanup_junk_files(dry_run=dry_run)
        
        # レポート表示
        report = cleaner.generate_cleanup_report(result)
        print(report)
        
        # ログファイルに保存
        log_file = Path(args.project_root) / 'logs' / f'cleanup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
        log_file.parent.mkdir(exist_ok=True)
        
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        logger.info(f"Cleanup report saved to: {log_file}")
        
    except Exception as e:
        logger.error(f"Cleanup failed: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
