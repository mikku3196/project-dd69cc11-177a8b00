"""
データベースマイグレーション設定
Alembicを使用したスキーマ管理
"""
import os
from alembic import command
from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
import logging

logger = logging.getLogger(__name__)

def get_alembic_config():
    """Alembic設定を取得"""
    alembic_cfg = Config("alembic.ini")
    return alembic_cfg

def create_migration(message: str):
    """新しいマイグレーションを作成"""
    try:
        alembic_cfg = get_alembic_config()
        command.revision(alembic_cfg, message=message, autogenerate=True)
        logger.info(f"Migration created: {message}")
    except Exception as e:
        logger.error(f"Failed to create migration: {e}")
        raise

def upgrade_database(revision: str = "head"):
    """データベースをアップグレード"""
    try:
        alembic_cfg = get_alembic_config()
        command.upgrade(alembic_cfg, revision)
        logger.info(f"Database upgraded to: {revision}")
    except Exception as e:
        logger.error(f"Failed to upgrade database: {e}")
        raise

def downgrade_database(revision: str):
    """データベースをダウングレード"""
    try:
        alembic_cfg = get_alembic_config()
        command.downgrade(alembic_cfg, revision)
        logger.info(f"Database downgraded to: {revision}")
    except Exception as e:
        logger.error(f"Failed to downgrade database: {e}")
        raise

def get_current_revision():
    """現在のリビジョンを取得"""
    try:
        alembic_cfg = get_alembic_config()
        script = ScriptDirectory.from_config(alembic_cfg)
        with alembic_cfg.get_main_option("sqlalchemy.url") as connection:
            context = MigrationContext.configure(connection)
            current_rev = context.get_current_revision()
            return current_rev
    except Exception as e:
        logger.error(f"Failed to get current revision: {e}")
        return None

def get_migration_history():
    """マイグレーション履歴を取得"""
    try:
        alembic_cfg = get_alembic_config()
        script = ScriptDirectory.from_config(alembic_cfg)
        return script.get_revisions()
    except Exception as e:
        logger.error(f"Failed to get migration history: {e}")
        return []

def init_migrations():
    """マイグレーションを初期化"""
    try:
        # 初回マイグレーション作成
        create_migration("Initial migration")
        logger.info("Migrations initialized")
    except Exception as e:
        logger.error(f"Failed to initialize migrations: {e}")
        raise

if __name__ == "__main__":
    # テスト実行
    init_migrations()
