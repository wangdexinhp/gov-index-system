python manage.py makemigrations coredata
生成迁移文件，需要再次迁移。
python manage.py migrate coredata

重新开始的步骤
-- 删除所有coredata开头的表
SET FOREIGN_KEY_CHECKS = 0;
DROP TABLE IF EXISTS 
    coredata_indicator,
    coredata_compositescoreformula,
    coredata_cityrank,
    coredata_city,
    coredata_province;
SET FOREIGN_KEY_CHECKS = 1;

-- 清理迁移记录
DELETE FROM django_migrations WHERE app = 'coredata';

-- 确认删除成功
SHOW TABLES LIKE 'coredata_%';
